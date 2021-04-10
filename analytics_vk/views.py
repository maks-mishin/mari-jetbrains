import csv
import calendar
from django.shortcuts import render
from datetime import datetime as dt, timedelta
import os
import requests
import time

from mari_jetbrains.settings import TOKEN, VERSION, DOMAIN


def most_comments(request):
    if request.method == 'POST':
        daterange = request.POST.get('daterange')
        date_from, date_to = daterange.split(' - ')
    else:
        now = dt.now()
        count_days = calendar.monthrange(now.year, now.month)[1]

        date_from = (now - timedelta(days=now.day-1)).strftime('%d.%m.%Y')
        date_to = (now + timedelta(days=count_days - now.day)).strftime('%d.%m.%Y')

    context = {}
    comments = csv_reader('data_file')

    users_comments = {}

    for comment in comments:
        if dt.strptime(date_from, '%d.%m.%Y') <= \
                dt.strptime(comment['date'], '%d.%m.%Y') <= \
                dt.strptime(date_to, '%d.%m.%Y'):
            if users_comments.get(comment['from_id']) is None:
                users_comments[comment['from_id']] = 1
            else:
                users_comments[comment['from_id']] += 1

    context['labels'] = list(users_comments.keys())
    context['data'] = list(users_comments.values())
    context['type_chart'] = 'bar'
    context['title'] = 'Users with the most comments'
    context['x_label'] = "User ID"
    context['y_label'] = 'Count comments'

    return render(request,
                  'dashboard.html',
                  context=context)


def unique_users(request):
    if request.method == 'POST':
        daterange = request.POST.get('daterange')
        date_from, date_to = daterange.split(' - ')
    else:
        now = dt.now()
        count_days = calendar.monthrange(now.year, now.month)[1]

        date_from = (now - timedelta(days=now.day-1)).strftime('%d.%m.%Y')
        date_to = (now + timedelta(days=count_days - now.day)).strftime('%d.%m.%Y')

    context = {}
    comments = csv_reader('data_file')

    users_unique = {}

    for comment in comments:
        if dt.strptime(date_from, '%d.%m.%Y') <= \
                dt.strptime(comment['date'], '%d.%m.%Y') <= \
                dt.strptime(date_to, '%d.%m.%Y'):
            if users_unique.get(comment['date']) is None:
                users_unique[comment['date']] = {comment['from_id']}
            else:
                users_unique[comment['date']].add(comment['from_id'])

    context['labels'] = list(users_unique.keys())
    context['data'] = [len(i) for i in users_unique.values()]
    context['type_chart'] = 'line'
    context['title'] = 'Unique users participating in discussions by day'
    context['x_label'] = 'Date'
    context['y_label'] = 'Unique users'

    return render(request,
                  'dashboard.html',
                  context=context)


def comments_by_days(request):
    if request.method == 'POST':
        daterange = request.POST.get('daterange')
        date_from, date_to = daterange.split(' - ')
    else:
        now = dt.now()
        count_days = calendar.monthrange(now.year, now.month)[1]

        date_from = (now - timedelta(days=now.day-1)).strftime('%d.%m.%Y')
        date_to = (now + timedelta(days=count_days - now.day)).strftime('%d.%m.%Y')

    context = {}
    comments = csv_reader('data_file')

    date_comments = {}

    for comment in comments:
        if dt.strptime(date_from, '%d.%m.%Y') <= \
                dt.strptime(comment['date'], '%d.%m.%Y') <= \
                dt.strptime(date_to, '%d.%m.%Y'):
            if date_comments.get(comment['date']) is None:
                date_comments[comment['date']] = {comment['id']}
            else:
                date_comments[comment['date']].add(comment['id'])

    context['labels'] = list(date_comments.keys())
    context['data'] = [len(i) for i in date_comments.values()]
    context['type_chart'] = 'line'
    context['title'] = 'Number of new comments by day'
    context['x_label'] = 'Date'
    context['y_label'] = 'Count comments'

    return render(request,
                  'dashboard.html',
                  context=context)


def get_comments(token: str, version: str, domain: str, count_posts) -> list:
    offset = 0
    posts = []
    comments = []

    while offset < count_posts:
        response = requests.get(
            'https://api.vk.com/method/wall.get',
            params={
                'access_token': token,
                'v': version,
                'domain': domain,
                'count': 100,
                'offset': offset
            }
        )
        # response.json() - convert json-object to dict
        data = response.json()['response']['items']
        offset += 100
        posts.extend(data)
        time.sleep(0.5)

    # перебираем все посты
    for post in posts:
        post_id = post['id']
        owner_id = post['owner_id']

        comments_count = post['comments']['count']  # количество комментов конкретного поста
        offset = 0

        while offset < comments_count:
            response = requests.get(
                'https://api.vk.com/method/wall.getComments',
                params={
                    'access_token': token,
                    'v': version,
                    'owner_id': owner_id,
                    'post_id': post_id,
                    'count': 100,
                    'offset': offset
                }
            )
            # response.json() - convert json-object to dict
            data = response.json()['response']['items']
            offset += 100
            comments.extend(data)
            time.sleep(0.2)
    return comments


def timestamp_to_date(date_timestamp):
    return dt.utcfromtimestamp(date_timestamp).strftime('%d.%m.%Y')


def csv_writer(comments: list, filename: str) -> None:
    with open(filename + '.csv', 'w', encoding='utf-8') as file:
        a_pen = csv.writer(file)
        a_pen.writerow(('id', 'from_id', 'date'))
        for comment in comments:
            try:
                a_pen.writerow((comment['id'], comment['from_id'], timestamp_to_date(comment['date'])))
            except KeyError:
                continue


def csv_reader(filename: str) -> list:
    comments = []
    with open('analytics_vk/' + filename + '.csv', newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            comments.append({
                'id': int(row['id']),
                'from_id': int(row['from_id']),
                'date': row['date']
            })
    return sorted(comments, key=lambda x: dt.strptime(x['date'], '%d.%m.%Y'))


if __name__ == '__main__':
    response = requests.get(
        'https://api.vk.com/method/wall.get',
        params={
            'access_token': TOKEN,
            'v': VERSION,
            'domain': DOMAIN
        }
    )
    count_posts_group = response.json()['response']['count']
    comments = get_comments(TOKEN, VERSION, DOMAIN, count_posts_group)

    csv_writer(comments, 'data_file')
