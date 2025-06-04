
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .services.main import run_ai_function
from django.utils.dateparse import parse_datetime
from rest_framework import status
from django.utils import timezone
from .serializers import PersonSerializer, CameraSerializer
from .models import Person, Camera, PersonVisiting
# Face login shared imports
from .services.face_login.face_login import (
    start_all_camera_threads,
    process_login,
    camera_frames,
    camera_locks
)
from .services.add_cam.add_cam import get_all_cameras
import time


class RunAIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        input_data = request.data.get("input")
        result = run_ai_function(input_data)
        return Response({"result": result})

class PersonCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        people = Person.objects.all()
        serializer = PersonSerializer(people, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = PersonSerializer(data=request.data)
        if serializer.is_valid():
            person = serializer.save()
            return Response({
                'message': 'Person created successfully',
                'person_id': person.id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)      

class PersonDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Person, pk=pk)

    def get(self, request, pk):
        person = self.get_object(pk)
        serializer = PersonSerializer(person, context={'request': request})
        return Response(serializer.data)

    def put(self, request, pk):
        person = self.get_object(pk)
        
        # ----------- Step 1: Update Person fields -----------
        person_fields = {}
        person_field_names = ['name', 'mobile_no', 'gender', 'company', 'id_no', 'email']
        
        for field in person_field_names:
            if field in request.data:
                person_fields[field] = request.data[field]
        
        if person_fields:
            serializer = PersonSerializer(person, data=person_fields, partial=True, context={'request': request})
            if serializer.is_valid():
                serializer.save()
            else:
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # ----------- Step 2: Update or create PersonVisiting fields -----------
        visiting_fields = {}
        visiting_field_names = ['visit_start_date', 'visit_end_date', 'visit_reason', 'card_no', 'visit_group', 'respondent']
        
        for field in visiting_field_names:
            if field in request.data:
                visiting_fields[field] = request.data[field]

        if visiting_fields:
            try:
                # Optional: convert date/time strings if needed
                if 'visit_start_date' in visiting_fields and isinstance(visiting_fields['visit_start_date'], str):
                    visiting_fields['visit_start_date'] = parse_datetime(visiting_fields['visit_start_date'])
                if 'visit_end_date' in visiting_fields and isinstance(visiting_fields['visit_end_date'], str):
                    visiting_fields['visit_end_date'] = parse_datetime(visiting_fields['visit_end_date'])

                # Try to get existing PersonVisiting record
                visiting_obj, created = PersonVisiting.objects.get_or_create(person=person)

                for key, value in visiting_fields.items():
                    setattr(visiting_obj, key, value)

                visiting_obj.save()

            except Exception as e:
                return Response({'error': f'Failed to update/create PersonVisiting record: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
        
        # ----------- Step 3: Final response -----------
        if not person_fields and not visiting_fields:
            return Response({'message': 'No data provided to update or create'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'Person updated and/or PersonVisiting record updated/created successfully'})

    def delete(self, request, pk):
        person = self.get_object(pk)
        person.delete()
        return Response({'message': 'Person deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

class CameraCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cameras = Camera.objects.all()
        serializer = CameraSerializer(cameras, many=True, context={'request': request})
        return Response(serializer.data)

    def post(self, request, format=None):
        serializer = CameraSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            camera = serializer.save()
            return Response({
                'message': 'Camera created successfully',
                'camera_id': camera.id
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CameraDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        return get_object_or_404(Camera, pk=pk)

    def get(self, request, pk):
        camera = self.get_object(pk)
        serializer = CameraSerializer(camera, context={'request': request})
        return Response(serializer.data)

    def put(self, request, pk):
        camera = self.get_object(pk)
        serializer = CameraSerializer(camera, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response({'message': 'Camera updated successfully'})
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        camera = self.get_object(pk)
        camera.delete()
        return Response({'message': 'Camera deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
    

class FaceLoginAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        start_all_camera_threads()
        camera_urls = get_all_cameras()
        results = []

        try:
            for cam_id in camera_urls:
                frame = camera_frames.get(cam_id)
                lock = camera_locks.get(cam_id)

                if frame is not None and lock is not None:
                    with lock:
                        result = process_login(cam_id, frame)
                        if result:
                            print(f"[LOGIN] {result}")
                            results.append(result)

            return Response({"logins": results})
        except Exception as e:
            return Response({"error": str(e)}, status=500)

