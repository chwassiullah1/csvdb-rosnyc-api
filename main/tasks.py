from celery import shared_task
from .models import Property, AutomatedTask
import logging
import requests  # just for starter demo (instead of full scrapy runner)

logger = logging.getLogger(__name__)


@shared_task(bind=True)
def run_automated_ads(self, account, neighborhoods, unit_types,apartment_types, ads_per_neighborhood, building_cap):
    def save_log(message, neighborhood=None, status=None, result=None):
        task, _ = AutomatedTask.objects.get_or_create(task_id=self.request.id)

        logs = task.logs or {}
        if neighborhood:
            logs.setdefault(neighborhood, [])
            logs[neighborhood].append(message)
        else:
            logs.setdefault("general", [])
            logs["general"].append(message)

        task.logs = logs
        if status:
            task.status = status
        if result is not None:
            task.result = result

        task.save(update_fields=["logs", "status", "result"])
        logger.info(f"[{self.request.id}] {neighborhood or 'general'} - {message}")

    neighborhood_urls = {}
    total_urls = 0

    try:
        save_log("Task started...")

        for n in neighborhoods:
            save_log(f"Fetching properties for {n}", neighborhood=n)
            urls = Property.objects.filter(area=n).values_list("url", flat=True).distinct()
            urls_list = list(urls)
            urls = []
            for url in urls_list:
                urls.append({'url': url, 'is_processed': 0})
            neighborhood_urls[n] = {
                "urls": urls,
                "count": len(urls_list),
                "progress": 0
            }
            total_urls += len(urls_list)

            save_log(f"Fetched {len(urls_list)} URLs for {n}", neighborhood=n)

            # iterate over urls & simulate scrapy requests
            # for i, url in enumerate(urls_list, start=1):
            #     try:
            #         save_log(f"Scraping {url} ({i}/{len(urls_list)})", neighborhood=n)

            #         # 🚀 for starter, just do a GET request
            #         resp = requests.get(url, timeout=15)
            #         save_log(f"Got response from {resp.url} [status={resp.status_code}]", neighborhood=n)

            #     except Exception as e:
            #         save_log(f"Error scraping {url}: {str(e)}", neighborhood=n)

            #     # update progress in DB
            #     neighborhood_urls[n]["progress"] = i
        task = AutomatedTask.objects.get(task_id=self.request.id)
        task.result = {"neighborhood_urls": neighborhood_urls}
        task.status = "PENDING"
        task.save(update_fields=["result"])

        result = {
            "neighborhood_urls": neighborhood_urls,
            "total_matching_urls": total_urls
        }

        save_log("Task added successfully!", status="PENDING", result=result)
        return result

    except Exception as e:
        error_msg = f"Error: {str(e)}"
        save_log(error_msg, status="FAILURE", result={"error": str(e)})
        raise e
