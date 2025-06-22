from django.shortcuts import render
from rest_framework import status
from django.contrib.auth.models import User
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from rest_framework import serializers
from .serializers import UserSerializers


class RegisterInputSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(min_length=6, required=True)
    username = serializers.CharField(max_length=150, required=True)
    first_name = serializers.CharField(max_length=30, required=False)
    last_name = serializers.CharField(max_length=30, required=False)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email already exists")
        return value

@api_view(['POST'])
@csrf_exempt
def register_view(request):
    serializer = RegisterInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.create_user(
            username=serializer.validated_data['username'],
            email=serializer.validated_data['email'],
            password=serializer.validated_data['password'],
            first_name=serializer.validated_data.get('first_name', ''),
            last_name=serializer.validated_data.get('last_name', '')
        )
        
        login(request, user)

        return Response({
            'status': True,
            'status_code': status.HTTP_201_CREATED,
            'result': {
                'message': 'User registered successfully',
                'user': UserSerializers.ModelSerializer(user).data
            }
        })
    except Exception as e:
        return Response({
            'status': False,
            'status_code': status.HTTP_400_BAD_REQUEST,
            'result': str(e)
        })


class LoginInputSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

@api_view(['POST'])
@csrf_exempt
def login_view(request):
    serializer = LoginInputSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    username = serializer.validated_data['username']
    password = serializer.validated_data['password']
    
    user = authenticate(request, username=username, password=password)
    
    if user is not None:
        login(request, user)
        return Response({
            'status': True,
            'status_code': status.HTTP_200_OK,
            'result': {
                'message': 'Login successful',
                'user': UserSerializers.ModelSerializer(user).data
            }
        })
    else:
        return Response({
            'status': False,
            'status_code': status.HTTP_401_UNAUTHORIZED,
            'result': 'Invalid username or password'
        })


@api_view(['POST'])
@login_required
def logout_view(request):
    logout(request)
    return Response({
        'status': True,
        'status_code': status.HTTP_200_OK,
        'result': 'Logout successful'
    })


@api_view(['GET'])
@login_required
def profile_view(request):
    return Response({
        'status': True,
        'status_code': status.HTTP_200_OK,
        'result': UserSerializers.ModelSerializer(request.user).data
    })
