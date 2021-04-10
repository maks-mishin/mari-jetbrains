import csv
import calendar
import os
import time
from django.shortcuts import render
import requests
from datetime import datetime as dt, timedelta


def most_comments(request):
    if request.method == 'POST':
        daterange = request.POST.get('daterange')
        date_from, date_to = daterange.split(' - ')
    else:
        now = dt.now()
        count_days = calendar.monthrange(now.year, now.month)[1]
        print("Count_days: ", count_days)

        date_from = (now - timedelta(days=now.day-1)).strftime('%d.%m.%Y')
        date_to = (now + timedelta(days=count_days - now.day)).strftime('%d.%m.%Y')
        print(date_from, date_to)

    context = {}
    comments = csv_reader('tproger_web')

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
        print("Count_days: ", count_days)

        date_from = (now - timedelta(days=now.day-1)).strftime('%d.%m.%Y')
        date_to = (now + timedelta(days=count_days - now.day)).strftime('%d.%m.%Y')
        print(date_from, date_to)

    context = {}
    comments = csv_reader('tproger_web')

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
        print("Count_days: ", count_days)

        date_from = (now - timedelta(days=now.day-1)).strftime('%d.%m.%Y')
        date_to = (now + timedelta(days=count_days - now.day)).strftime('%d.%m.%Y')
        print(date_from, date_to)

    context = {}
    comments = csv_reader('tproger_web')

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
    """

    :param token: token of VK API application
    :param version: version of VK API
    :param domain: short address of the community
    :param count_posts: number of posts
    :return: list of comments from the community
    """
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
        print('Posts', len(posts))
    #   =================== список всех постов сформирован ============

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
            print('Comments', len(comments))
    return comments


def get_likes():
    pass


def timestamp_to_date(date_timestamp):
    """

    :param date_timestamp: date in timestamp format
    :return: date in utc format
    """
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
    token = '48e587ba48e587ba48e587ba744892ba21448e548e587ba288eb70ac2421ceb8317b891'
    version = '5.130'
    domain = 'tproger_web'

    response = requests.get(
        'https://api.vk.com/method/wall.get',
        params={
            'access_token': token,
            'v': version,
            'domain': domain
        }
    )
    count_posts_group = response.json()['response']['count']

    # comments = get_comments(token, version, domain, count_posts_group)

    # csv_writer(comments, 'tproger_web')
    comments = csv_reader('tproger_web')
    print(len(comments))
