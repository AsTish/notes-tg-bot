from rest_framework import serializers
from .models import Note, Folder

class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ['id', 'title', 'content', 'created_at', 'updated_at', 'user', 'folder']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']  # id и временные пол€ только дл€ чтени€

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, "user"):
            validated_data['user'] = request.user  # ѕрив€зываем заметку к пользователю
        return super().create(validated_data)


class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ['id', 'name', 'user', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']  # id и временные пол€ только дл€ чтени€

    def create(self, validated_data):
        request = self.context.get('request')
        if request and hasattr(request, "user"):
            validated_data['user'] = request.user  # ѕрив€зываем папку к пользователю
        return super().create(validated_data)