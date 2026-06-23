from django import forms 
from .models import Refeicoes, Metas

class Refeicao_ia(forms.Form):
    descricao = forms.CharField(
        label = "Informe sua refeição",
        widget = forms.Textarea(attrs={
            'rows' : 3,
            #'placeholder': 'Ex: Comi 2 ovos mexidos e um copo de leite...'
        })
    )

class Definir_metas_form(forms.ModelForm):
    class Meta:
        model = Metas
        fields = ['meta_calorias', 'meta_proteinas']

        widgets = {
            'meta_calorias': forms.NumberInput(attrs={'placeholder': 'Ex: 2000'}),
            'meta_proteinas': forms.NumberInput(attrs={'placeholder': 'Ex: 150'}),
        }
        labels = {
            'meta_calorias': 'Meta Diária de Calorias (kcal)',
            'meta_proteinas': 'Meta Diária de Proteínas (g)',
        }
