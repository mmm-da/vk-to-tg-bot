from celery import Celery
app = Celery(
    "app",
    include=[
        "app.poster_tasks",
        "app.puller_tasks",
        "app.vk_api_helpers"
    ],
)

app.conf.broker_url = f"redis://@localhost:7000/0"
app.conf.result_backend = f"redis://@localhost:7000/0"

app.conf.beat_schedule = {
    'pull-vk-posts': {
        'task': 'app.puller_tasks.pull_vk_posts',
        'schedule': 300.0
    },
}

if __name__ == "__main__":
    app.start()