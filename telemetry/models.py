from django.db import models


class TelemetryLog(models.Model):
    timestamp = models.DateTimeField(auto_now_add=True)
    catfish_count = models.IntegerField()
    ph = models.FloatField()
    temperature = models.FloatField()
    turbidity = models.FloatField()
    tds = models.FloatField()
    status = models.CharField(max_length=50)
    recommendation = models.TextField()

    class Meta:
        ordering = ["-timestamp"]


class BiomassRecord(models.Model):
    date = models.DateField(auto_now_add=True)
    total_fish_count = models.IntegerField(default=250)
    avg_fish_weight_kg = models.FloatField(default=0.00736)  # 1.84kg / 250 ekor
    feed_given_kg = models.FloatField()
    fcr_value = models.FloatField()
    cost_saved_idr = models.IntegerField()

    class Meta:
        ordering = ["-date", "-id"]
