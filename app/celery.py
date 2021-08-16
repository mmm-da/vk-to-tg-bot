from celery import Celery
import os

app = Celery(
    "app",
    include=[
        "app.poster_tasks",
        "app.puller_tasks",
        "app.vk_api_helpers"
    ],
)

redis_host = os.environ.get('REDIS_HOST', 'redis')

app.conf.broker_url = f'redis://@{redis_host}:7000/0'
app.conf.result_backend = f'redis://@{redis_host}:7000/0'

app.conf.beat_schedule = {
    'pull-vk-posts': {
        'task': 'app.puller_tasks.pull_vk_posts',
        'schedule': 10.0
    },
}

if __name__ == "__main__":
    app.start()