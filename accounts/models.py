from django.contrib.auth.models import AbstractUser, Group, Permission,BaseUserManager,AbstractBaseUser
from django.db import models
from django.conf import settings
# class User(AbstractUser):
#     email = models.EmailField(unique=True)
#     phone_number = models.CharField(max_length=15)
#     gender = models.CharField(max_length=10)

#     # Avoid clashes with Django's default user model by adding related_name
#     groups = models.ManyToManyField(
#         Group,
#         related_name='custom_user_groups',  # Use a unique related_name
#         blank=True
#     )
#     user_permissions = models.ManyToManyField(
#         Permission,
#         related_name='custom_user_permissions',  # Use a unique related_name
#         blank=True
#     )

#     USERNAME_FIELD = 'email'
#     REQUIRED_FIELDS = ['first_name', 'last_name', 'phone_number']

#     def __str__(self):
#         return self.email

class UserManager(BaseUserManager):
    def create_user(self, email, name, password=None,password2=None,gender=None, phone_number=None):
        """
        Creates and saves a User with the given email, date of
        birth and password.
        """
        if not email:
            raise ValueError("Users must have an email address")

        user = self.model(
            email=self.normalize_email(email),
            name=name,
            gender=gender,
            phone_number=phone_number 
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, password=None):
        """
        Creates and saves a superuser with the given email, date of
        birth and password.
        """
        user = self.create_user(
            email,
            password=password,
            name=name
        )
        user.is_admin = True
        user.save(using=self._db)
        return user


class User(AbstractBaseUser):
    email = models.EmailField(
        verbose_name="email address",
        max_length=255,
        unique=True,
    )
    name = models.CharField(max_length=200)
    gender = models.CharField(max_length=10, choices=[('male', 'Male'), ('female', 'Female'), ('other', 'Other')],blank=True, 
    null=True)
    phone_number = models.CharField(max_length=20,blank=True, 
    null=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    created_at=models.DateTimeField(auto_now_add=True)
    updated_at=models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        "Does the user have a specific permission?"
        # Simplest possible answer: Yes, always
        return True

    def has_module_perms(self, app_label):
        "Does the user have permissions to view the app `app_label`?"
        # Simplest possible answer: Yes, always
        return True

    @property
    def is_staff(self):
        "Is the user a member of staff?"
        # Simplest possible answer: All admins are staff
        return self.is_admin
    class Meta:
        app_label = 'accounts'
    
class Transaction(models.Model):
    TRANSACTION_TYPE_CHOICES = [
        ('expense', 'Expense'),
        ('income', 'Income'),
    ]
    
    ENTRY_METHOD_CHOICES = [
        ('manual', 'Manual'),
        ('voice', 'Voice'),
        ('image', 'Image'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    transaction_type = models.CharField(max_length=10, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    description = models.CharField(max_length=255)  # reason for earning or spending
    entry_method = models.CharField(max_length=10, choices=ENTRY_METHOD_CHOICES)  # manual, voice, or image
    timestamp = models.DateTimeField(auto_now_add=True)  # exact time and date of transaction
    # receipt_image = models.ImageField(upload_to='receipts/', blank=True, null=True)  # optional field for uploaded image
    # voice_text = models.TextField(blank=True, null=True)  # optional field for extracted voice command text

    class Meta:
        ordering = ['-timestamp']  # Most recent transactions first for faster querying in history
    
    def __str__(self):
        return f"{self.user.email} - {self.transaction_type} - {self.amount}"    