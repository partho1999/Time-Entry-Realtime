from rest_framework import serializers
from .models import Person, PersonImage, PersonVisiting, Camera 

class PersonImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonImage
        fields = ['image']

class PersonVisitingSerializer(serializers.ModelSerializer):
    class Meta:
        model = PersonVisiting
        fields = [
            'card_no',
            'visit_start_time',
            'visit_end_time',
            'visitor_group',
            'visit_reason',
            'respondent'
        ]

class PersonSerializer(serializers.ModelSerializer):
    # Write-only input fields
    image = serializers.ImageField(write_only=True, required=False)
    visiting_info = PersonVisitingSerializer(write_only=True, required=False)

    # Read-only output fields
    image_url = serializers.SerializerMethodField(read_only=True)
    image_text = serializers.SerializerMethodField(read_only=True)  # add this

    class Meta:
        model = Person
        fields = [
            'id',
            'name',
            'mobile_no',
            'gender',
            'company',
            'id_no',
            'email',
            'image',          # input only
            'visiting_info',  # input only
            'image_url',      # output only
            'image_text',     # output only
        ]

    def get_image_url(self, obj):
        if hasattr(obj, 'image') and obj.image.image:
            request = self.context.get('request', None)
            if request:
                return request.build_absolute_uri(obj.image.image.url)
            return obj.image.image.url
        return None

    def get_image_text(self, obj):
        if hasattr(obj, 'image') and obj.image.image_text:
            return obj.image.image_text
        return None

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Add nested visiting_info output explicitly
        if hasattr(instance, 'visiting_info'):
            data['visiting_info'] = PersonVisitingSerializer(instance.visiting_info).data
        else:
            data['visiting_info'] = None
        return data

    def create(self, validated_data):
        image_file = validated_data.pop('image', None)
        visiting_data = validated_data.pop('visiting_info', None)

        person = Person.objects.create(**validated_data)

        if image_file:
            PersonImage.objects.create(person=person, image=image_file)

        if visiting_data:
            PersonVisiting.objects.create(person=person, **visiting_data)

        return person

    def update(self, instance, validated_data):
        image_file = validated_data.pop('image', None)
        visiting_data = validated_data.pop('visiting_info', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Update or create PersonImage
        if image_file:
            if hasattr(instance, 'image'):
                instance.image.image = image_file
                instance.image.save()
            else:
                PersonImage.objects.create(person=instance, image=image_file)

        # Update or create PersonVisiting
        if visiting_data:
            visiting_obj, _ = PersonVisiting.objects.get_or_create(person=instance)
            for attr, value in visiting_data.items():
                setattr(visiting_obj, attr, value)
            visiting_obj.save()

        return instance

class CameraSerializer(serializers.ModelSerializer):
    class Meta:
        model = Camera
        fields = '__all__'  # or list each field explicitly for more control

        # Optional: mark cam_password as write-only if you don't want to expose it in responses
        extra_kwargs = {
            'cam_password': {'write_only': True}
        }