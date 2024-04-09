# schema.py
import graphene
from graphene_django import DjangoObjectType
from graphql_auth.schema import UserQuery, MeQuery
from .models import BlogPost, User
from graphql_jwt.decorators import login_required
from graphql_jwt.shortcuts import get_token
from graphql_auth import mutations


class UserType(DjangoObjectType):
    class Meta:
        model = User
        exclude = ('password',)

class BlogPostType(DjangoObjectType):
    class Meta:
        model = BlogPost

class Query(UserQuery, MeQuery, graphene.ObjectType):
    all_blog_posts = graphene.List(BlogPostType)
    blog_post = graphene.Field(BlogPostType, id=graphene.Int())
    all_users = graphene.List(UserType)  # Define a new field to query all users

    @login_required
    def resolve_all_blog_posts(self, info, **kwargs):
        return BlogPost.objects.all()

    @login_required
    def resolve_blog_post(self, info, id):
        return BlogPost.objects.get(pk=id)
    
    # Resolve the all_users field to return all users
    @login_required
    def resolve_all_users(self, info, **kwargs):
        return User.objects.all()

class CreateBlogPost(graphene.Mutation):
    class Arguments:
        title = graphene.String()
        subTitle = graphene.String()
        body = graphene.String()

    blog_post = graphene.Field(BlogPostType)

    @login_required
    def mutate(self, info, title, subTitle, body):
        user = info.context.user
        blog_post = BlogPost(title=title, subTitle=subTitle, body=body, user=user)
        blog_post.save()
        return CreateBlogPost(blog_post=blog_post)

class UpdateBlogPost(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)
        title = graphene.String()
        subTitle = graphene.String()
        body = graphene.String()

    blog_post = graphene.Field(BlogPostType)

    @login_required
    def mutate(self, info, id, title=None, subTitle=None, body=None):
        blog_post = BlogPost.objects.get(pk=id)
        if blog_post.user != info.context.user:
            raise Exception("You are not authorized to update this post.")
        if title:
            blog_post.title = title
        if subTitle:
            blog_post.subTitle = subTitle
        if body:
            blog_post.body = body
        blog_post.save()
        return UpdateBlogPost(blog_post=blog_post)

class DeleteBlogPost(graphene.Mutation):
    class Arguments:
        id = graphene.Int(required=True)

    success = graphene.Boolean()

    @login_required
    def mutate(self, info, id):
        blog_post = BlogPost.objects.get(pk=id)
        if blog_post.user != info.context.user:
            raise Exception("You are not authorized to delete this post.")
        blog_post.delete()
        return DeleteBlogPost(success=True)


class Login(graphene.Mutation):
    class Arguments:
        username = graphene.String(required=True)
        password = graphene.String(required=True)

    token = graphene.String()

    def mutate(self, info, username, password):
        from django.contrib.auth import authenticate
        user = authenticate(username=username, password=password)
        if user is None:
            raise Exception('Invalid credentials')
        token = get_token(user)
        return Login(token=token)


class AuthMutation(graphene.ObjectType):
    register = mutations.Register.Field()
    verify_account = mutations.VerifyAccount.Field()
    resend_activation_email = mutations.ResendActivationEmail.Field()
    send_password_reset_email = mutations.SendPasswordResetEmail.Field()
    password_reset = mutations.PasswordReset.Field()
    password_change = mutations.PasswordChange.Field()
    archive_account = mutations.ArchiveAccount.Field()
    delete_account = mutations.DeleteAccount.Field()
    update_account = mutations.UpdateAccount.Field()
    send_secondary_email_activation = mutations.SendSecondaryEmailActivation.Field()
    verify_secondary_email = mutations.VerifySecondaryEmail.Field()
    swap_emails = mutations.SwapEmails.Field()

    # django-graphql-jwt inheritances
    token_auth = mutations.ObtainJSONWebToken.Field()
    verify_token = mutations.VerifyToken.Field()
    refresh_token = mutations.RefreshToken.Field()
    revoke_token = mutations.RevokeToken.Field()

class Mutation(AuthMutation, graphene.ObjectType):
    create_blog_post = CreateBlogPost.Field()
    update_blog_post = UpdateBlogPost.Field()
    delete_blog_post = DeleteBlogPost.Field()
    login = Login.Field()


schema = graphene.Schema(query=Query, mutation=Mutation)
