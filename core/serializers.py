from djoser.serializers import UserCreateSerializer

class CustomUserCreateSerializer(UserCreateSerializer):
    # overriding the meta class in usercreateserializer
    class Meta(UserCreateSerializer.Meta):
        fields = ["id", "email", "first_name", "last_name", "password", "username"]
        