from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.contrib.auth.models import User

class Refeicoes(models.Model):
    # on_delete=models.CASCADE significa: se o usuário for deletado, apague as refeições dele também.
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    descricao = models.CharField(max_length=100)
    calorias = models.IntegerField(default=0)
    proteinas = models.FloatField(default=0.0)
    data = models.DateField(default=timezone.now)

    def __str__(self):
        return f"{self.usuario.username} - {self.descricao}"

class Metas(models.Model):
    # OneToOneField Um usuário só pode ter uma única configuração de metas diárias (1 para 1 Exclusivo)
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    meta_calorias = models.IntegerField(default=0)
    meta_proteinas = models.FloatField(default=0)

    