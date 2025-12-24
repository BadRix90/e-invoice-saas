from rest_framework import serializers
from .models import Tenant, User


class TenantSerializer(serializers.ModelSerializer):
    logo = serializers.SerializerMethodField()

    class Meta:
        model = Tenant
        fields = [
            'id', 'name', 'slug',
            'company_name', 'street', 'zip_code', 'city', 'country',
            'tax_id', 'vat_id',
            'email', 'phone',
            'bank_name', 'iban', 'bic',
            'logo',
        ]
        read_only_fields = ['id', 'slug']

    def get_logo(self, obj):
        if obj.logo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.logo.url)
            return obj.logo.url
        return None


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    company_code = serializers.CharField(write_only=True)
    company_name = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            "username",
            "email",
            "password",
            "password2",
            "company_code",
            "company_name",
            "first_name",
            "last_name",
        )

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        company_code = validated_data.pop("company_code")
        company_name = validated_data.pop("company_name", "")
        validated_data.pop("password2")

        tenant = Tenant.objects.filter(slug=company_code).first()

        if not tenant:
            if not company_name:
                raise serializers.ValidationError({"company_name": "Company name is required for new tenants."})

            tenant = Tenant.objects.create(
                name=company_name,
                slug=company_code,
                company_name=company_name,
                email=validated_data["email"],
            )

            user_role = "owner"
            is_staff = True
        else:
            user_role = "user"
            is_staff = False

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            tenant=tenant,
            is_staff=is_staff,
            role=user_role,  
        )

        return user


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'role', 'date_joined']
        read_only_fields = ['id', 'date_joined']