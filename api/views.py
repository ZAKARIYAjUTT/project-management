from django.contrib.auth.models import User
from rest_framework import generics, viewsets, permissions, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .models import Project, Task, ProjectMembership
from .serializers import UserSerializer, ProjectSerializer, TaskSerializer, ProjectMembershipSerializer


class UserCreateView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.filter(is_deleted=False)
    serializer_class = ProjectSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)

    @action(detail=True, methods=['post'])
    def add_user(self, request, pk=None):
        project = self.get_object()
        user = User.objects.get(id=request.data['user_id'])
        membership, created = ProjectMembership.objects.get_or_create(
            user=user,
            project=project,
            defaults={
                'can_create': request.data.get('can_create', False),
                'can_edit': request.data.get('can_edit', False),
                'can_delete': request.data.get('can_delete', False),
                'can_add_users': request.data.get('can_add_users', False),
            }
        )
        if not created:
            # Update existing membership
            membership.can_create = request.data.get('can_create', membership.can_create)
            membership.can_edit = request.data.get('can_edit', membership.can_edit)
            membership.can_delete = request.data.get('can_delete', membership.can_delete)
            membership.can_add_users = request.data.get('can_add_users', membership.can_add_users)
            membership.save()

        response_data = {
            'user_id': user.id,
            'username': user.username,
            'project_id': project.id,
            'project_name': project.name,
            'permissions': {
                'can_create': membership.can_create,
                'can_edit': membership.can_edit,
                'can_delete': membership.can_delete,
                'can_add_users': membership.can_add_users
            }
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.filter(is_deleted=False)
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_destroy(self, instance):
        instance.soft_delete()


class ProjectMembershipViewSet(viewsets.ModelViewSet):
    queryset = ProjectMembership.objects.all()
    serializer_class = ProjectMembershipSerializer
    permission_classes = [permissions.IsAuthenticated]
