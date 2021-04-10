from django.urls import path

from analytics_vk.views import most_comments, \
    unique_users, comments_by_days

urlpatterns = [
    path('comments-days/', comments_by_days, name='comments_by_days'),
    path('most-comments/', most_comments, name='most_comments'),
    path('unique-users/', unique_users, name='unique_users')
]
