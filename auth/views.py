from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer


@api_view(['POST'])
@csrf_exempt
def register_view(request):
    serializer = UserRegistrationSerializer(data=request.data)
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
        
        # Automatically log in the user after registration
        login(request, user)
        
        return Response({
            'status': True,
            'status_code': status.HTTP_201_CREATED,
            'result': {
                'message': 'User registered successfully',
                'user': UserProfileSerializer(user).data
            }
        })
    except Exception as e:
        return Response({
            'status': False,
            'status_code': status.HTTP_400_BAD_REQUEST,
            'result': str(e)
        })


@api_view(['POST'])
@csrf_exempt
def login_view(request):
    serializer = UserLoginSerializer(data=request.data)
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
                'user': UserProfileSerializer(user).data
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
        'result': UserProfileSerializer(request.user).data
    })
