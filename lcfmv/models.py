from django.db import models
from api.components import Link
from django.core.exceptions import ValidationError


class EstadoManager(models.Manager):
    pass


class Estado(models.Model):
    sigla = models.CharField('Sigla', max_length=2)

    objects = EstadoManager()

    class Meta:
        verbose_name = 'Estado'
        verbose_name_plural = 'Estados'

    def __str__(self):
        return self.sigla


class TipoLegislacaoManager(models.Manager):
    pass


class TipoLegislacao(models.Model):
    descricao = models.CharField('Descrição', max_length=255)

    objects = TipoLegislacaoManager()

    class Meta:
        verbose_name = 'Tipo de Legislação'
        verbose_name_plural = 'Tipos de Legislação'

    def __str__(self):
        return self.descricao


class ConselhoManager(models.Manager):
    pass


class Conselho(models.Model):
    nome = models.CharField('Nome', max_length=255)
    sigla = models.CharField('Sigla', max_length=25)
    estado = models.ForeignKey(Estado, verbose_name='Estado', on_delete=models.CASCADE)

    objects = ConselhoManager()

    class Meta:
        verbose_name = 'Conselho'
        verbose_name_plural = 'Conselhos'

    def __str__(self):
        return '{} - {}'.format(self.sigla, self.nome)


class AcordaoManager(models.Manager):
    pass


class Acordao(models.Model):
    numero = models.CharField('Número', max_length=255)
    ano = models.IntegerField('Ano')
    data = models.DateField('Data')
    ementa = models.TextField('Ementa')
    conteudo = models.TextField('Conteúdo')
    arquivo = models.FileField('Arquivo', upload_to='acordao', null=True, blank=True)
    data_inclusao = models.DateField('Data de Inclusão', auto_now_add=True)
    processo = models.CharField('Processo', max_length=255)
    relator = models.CharField('Relator', max_length=255)

    objects = AcordaoManager()

    class Meta:
        verbose_name = 'Acordão'
        verbose_name_plural = 'Acordãos'

    def __str__(self):
        return self.get_descricao()

    def get_descricao(self):
        return 'Acordão {} de {}'.format(self.numero, self.data.strftime('%d/%m/%Y'))

    def get_arquivo(self):
        return Link(self.arquivo.url, target='_blank', icon='file-pdf')


class LegislacaoManager(models.QuerySet):
    def virgentes(self):
        return self.filter(revogada_por__isnull=True)

    def revogadas(self):
        return self.filter(revogada_por__isnull=False)


class Legislacao(models.Model):
    numero = models.CharField('Número', max_length=255)
    ano = models.IntegerField('Ano')
    tipo = models.ForeignKey(TipoLegislacao, verbose_name='Tipo', null=True, on_delete=models.CASCADE)
    data = models.DateField('Data')
    ementa = models.TextField('Ementa')
    conteudo = models.TextField('Conteúdo')
    arquivo = models.FileField('Arquivo', upload_to='acordao', null=True, blank=True)
    data_inclusao = models.DateField('Data de Inclusão', auto_now_add=True)

    data_dou = models.DateField('Data de Publicação')
    secao_dou = models.CharField('Seção da Publicação', max_length=100)
    pagina_dou = models.CharField('Página da Publicação', max_length=100)

    revogada_por = models.ForeignKey('lcfmv.legislacao', verbose_name='Revogada Por', null=True, blank=True, on_delete=models.CASCADE)

    objects = LegislacaoManager().as_manager()

    class Meta:
        verbose_name = 'Legislação'
        verbose_name_plural = 'Legislações'


    def __str__(self):
        return self.get_descricao()

    def get_descricao(self, incluir_removagacao=True):
        descricao = '{} {} de {}'.format(self.tipo, self.numero, self.data.strftime('%d/%m/%Y'))
        if self.revogada_por_id:
            descricao = '{}, revogada pela legislação "{}"'.format(descricao, self.revogada_por.get_descricao(incluir_removagacao=False))
        return descricao

    def get_arquivo(self):
        return Link(self.arquivo.url, target='_blank', icon='file-pdf') if self.arquivo else None

    def save(self, *args, **kwargs):
        if self.tipo.descricao == 'Resolução':
            if Legislacao.objects.filter(numero=self.numero, tipo__descricao='Resolução').exclude(pk=self.pk).exists():
                raise ValidationError('Já existe uma resolução com esse número')
        super().save(*args, **kwargs)