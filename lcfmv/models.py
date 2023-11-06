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


class RelatorManager(models.Manager):
    pass


class Relator(models.Model):
    nome = models.CharField('Nome', max_length=255)
    numero_crmv = models.CharField('Nº CRMV', max_length=25)
    classe = models.CharField('Classe', max_length=100, choices=[
        ['V', 'Médico-Veterinário'], ['Z', 'Zootecnista'],
    ])
    conselho = models.ForeignKey(Conselho, verbose_name='Conselho', on_delete=models.CASCADE)

    objects = RelatorManager()

    class Meta:
        verbose_name = 'Relator'
        verbose_name_plural = 'Relatores'

    def __str__(self):
        return '{} ({})'.format(self.nome, self.numero_crmv)


class AcordaoManager(models.Manager):
    pass


class Acordao(models.Model):

    ORGAO_JULGADOR_CHOICES = [['Plenário', 'Plenário'], ['Primeira Turma', 'Primeira Turma'], ['Segunda Turma', 'Segunda Turma']]
    NATUREZA_CHOICES = [['Processo Administrativo', 'Processo Administrativo'], ['Processo Ético-Profissional', 'Processo Ético-Profissional']]

    numero = models.CharField('Número', max_length=255)
    ano = models.IntegerField('Ano')
    relator = models.ForeignKey(Relator, verbose_name='Relator', on_delete=models.CASCADE)
    data_dou = models.DateField('Data de Publicação no DOU')
    orgao_julgador = models.CharField('Órgão Julgador', max_length=100, choices=ORGAO_JULGADOR_CHOICES)
    natureza = models.CharField('Natureza', max_length=100, choices=NATUREZA_CHOICES)
    ementa = models.TextField('Ementa')
    conteudo = models.TextField('Conteúdo')
    arquivo = models.FileField('Arquivo', upload_to='acordao', blank=False)
    processo = models.CharField('Processo', max_length=255)

    objects = AcordaoManager()

    class Meta:
        verbose_name = 'Acórdão'
        verbose_name_plural = 'Acórdãos'
        unique_together = [['numero', 'ano', 'natureza', 'orgao_julgador']]

    def __str__(self):
        return self.get_descricao()

    def get_descricao(self):
        return 'Acordão {} de {}'.format(self.numero, self.ano)

    def get_arquivo(self):
        try:
            return Link(self.arquivo.url, target='_blank', icon='file-pdf')
        except ValueError:
            return None


class LegislacaoManager(models.QuerySet):
    def virgentes(self):
        return self.filter(revogada_por__isnull=True)

    def revogadas(self):
        return self.filter(revogada_por__isnull=False)


class Legislacao(models.Model):
    numero = models.CharField('Número', max_length=255)
    ano = models.IntegerField('Ano')
    tipo = models.ForeignKey(TipoLegislacao, verbose_name='Tipo', on_delete=models.CASCADE)
    data = models.DateField('Data')
    ementa = models.TextField('Ementa')
    conteudo = models.TextField('Conteúdo')
    arquivo = models.FileField('Arquivo', upload_to='acordao', blank=False)

    data_dou = models.DateField('Data de Publicação', null=False)
    secao_dou = models.CharField('Seção da Publicação', max_length=100)
    pagina_dou = models.CharField('Página da Publicação', max_length=100)

    revogada_por = models.ForeignKey('lcfmv.legislacao', verbose_name='Revogada Por', null=True, blank=True, on_delete=models.CASCADE)

    codigo = models.IntegerField('Código', null=True)

    objects = LegislacaoManager().as_manager()

    class Meta:
        verbose_name = 'Legislação'
        verbose_name_plural = 'Legislações'
        unique_together = [['numero', 'ano', 'tipo']]


    def __str__(self):
        return self.get_descricao()

    def get_descricao(self, incluir_removagacao=True):
        descricao = '{} {} de {}'.format(self.tipo, self.numero, self.data.strftime('%d/%m/%Y'))
        if self.revogada_por_id:
            descricao = '{}, revogada pela legislação "{}"'.format(descricao, self.revogada_por.get_descricao(incluir_removagacao=False))
        return descricao

    def get_arquivo(self):
        try:
            return Link(self.arquivo.url, target='_blank', icon='file-pdf')
        except ValueError:
            return None

    def save(self, *args, **kwargs):
        if self.tipo.descricao == 'Resolução':
            if Legislacao.objects.filter(numero=self.numero, tipo__descricao='Resolução').exclude(pk=self.pk).exists():
                raise ValidationError('Já existe uma resolução com esse número')
        super().save(*args, **kwargs)