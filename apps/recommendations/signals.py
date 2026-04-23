from django.contrib.contenttypes.models import ContentType
from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.posts.models import Post
from apps.reactions.models import Reaction
from apps.watch.models import WatchVideo


@receiver(post_save, sender=Post)
def post_saved_recommendations(sender, instance, created, **kwargs):
    """New video post with category → small creator-affinity score; refresh cached profile snapshot."""
    from apps.recommendations.services import InterestService, InteractionService

    if created and instance.post_type == "video" and instance.category_id:
        InteractionService.record_upload_in_category(instance.author, instance.category_id)
    InterestService.refresh_profile_snapshot(instance.author)


@receiver(post_save, sender=WatchVideo)
def watch_video_saved_recommendations(sender, instance, created, **kwargs):
    from apps.recommendations.services import InterestService, InteractionService

    if created and instance.category_id:
        InteractionService.record_upload_in_category(instance.author, instance.category_id)
    InterestService.refresh_profile_snapshot(instance.author)


@receiver(post_save, sender=Reaction)
def reaction_saved_recommendations(sender, instance, created, **kwargs):
    """Like on a Post → category interest for the reacting user."""
    if not created:
        return
    if instance.content_type_id != ContentType.objects.get_for_model(Post).id:
        return
    post = Post.objects.filter(pk=instance.object_id).first()
    if not post:
        return
    from apps.recommendations.services import InterestService, InteractionService

    InteractionService.record_post_like(instance.user, post)
    InterestService.refresh_profile_snapshot(instance.user)
