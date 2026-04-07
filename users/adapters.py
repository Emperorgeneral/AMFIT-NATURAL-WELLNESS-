from django.contrib.auth import get_user_model
from django.utils.text import slugify
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class AmfitSocialAccountAdapter(DefaultSocialAccountAdapter):
    def _build_unique_username(self, base_username: str) -> str:
        UserModel = get_user_model()
        base = slugify(base_username or "user").replace("-", "") or "user"
        candidate = base
        suffix = 1
        while UserModel.objects.filter(username__iexact=candidate).exists():
            candidate = f"{base}{suffix}"
            suffix += 1
        return candidate

    def populate_user(self, request, sociallogin, data):
        user = super().populate_user(request, sociallogin, data)

        extra = sociallogin.account.extra_data or {}
        first_name = data.get("first_name") or extra.get("given_name") or ""
        last_name = data.get("last_name") or extra.get("family_name") or ""
        email = (data.get("email") or extra.get("email") or "").strip()

        if email and not user.email:
            user.email = email
        if first_name and not user.first_name:
            user.first_name = first_name
        if last_name and not user.last_name:
            user.last_name = last_name

        if not user.username:
            fallback = email.split("@")[0] if email else ""
            base_username = (
                data.get("username")
                or extra.get("preferred_username")
                or f"{first_name}{last_name}"
                or fallback
                or "user"
            )
            user.username = self._build_unique_username(base_username)

        return user
