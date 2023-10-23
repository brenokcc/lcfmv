from api import actions
from api.components import Boxes, Indicators
from .models import TipoLegislacao, Legislacao, Acordao
from api.models import Role


class AcessoRapido(actions.Action):
    def view(self):
        boxes = Boxes(title='Acesso Rápido')
        if self.requires('adm'):
            boxes.append(icon='users-line', label='Usuários', url='/api/v1/users/')
        if self.requires('adm', 'opl'):
            boxes.append(icon='list', label='Tipos de Legislação', url='/api/v1/tipolegislacao/')
        if self.requires('adm'):
            boxes.append(icon='building', label='Conselhos', url='/api/v1/conselho/')
        if self.requires('adm', 'opl'):
            boxes.append(icon='file-contract', label='Legislações', url='/api/v1/legislacao/')
        if self.requires('adm', 'opa'):
            boxes.append(icon='file-signature', label='Acordãos', url='/api/v1/acordao/')
        return boxes

    def has_permission(self):
        return self.user.is_authenticated


class Totais(actions.Action):
    def view(self):
        totais = Indicators('Legislação')
        for tipo in TipoLegislacao.objects.all():
            totais.append(tipo, Legislacao.objects.filter(tipo=tipo).count())
        totais.append('Acordão', Acordao.objects.count())
        return totais

    def has_permission(self):
        return True

class Dashboard(actions.ActionSet):
    actions = AcessoRapido, Totais

    def has_permission(self):
        return self.user.is_authenticated


class Consultar(actions.ActionView):
    tipo_documento = actions.ChoiceField(
        label='Tipo de Documento', choices=[
            ['legislacao', 'Legislação'],
            ['acordao', 'Acordão'],
        ], pick=True, initial='legislacao'
    )
    tipo_legislacao = actions.RelatedField(queryset=TipoLegislacao.objects, label='Tipo de Legislação', required=False, pick=True, help_text='Não informar caso deseje buscar em todos os tipos.')
    palavas_chaves = actions.CharField(label='Palavras-chaves', required=True)
    criterio_busca = actions.ChoiceField(
        label='Critério da Busca', choices=[
            ['toda', 'Contendo todas palavras'],
            ['qualquer', 'Contendo qualquer uma das palavras'],
            ['exato', 'Cotendo a expressão exata'],
        ], pick=True, initial='toda'
    )
    escopo_busca = actions.MultipleChoiceField(
        label='Escopo da Busca', choices=[
            ['numero', 'Número'],
            ['ementa', 'Ementa'],
            ['conteudo', 'Conteúdo'],
        ], pick=True, initial=['numero', 'ementa', 'conteudo']
    )

    class Meta:
        icon = 'file-contract'
        title = 'Consulta Pública'
        help_text = 'Busque pelas legislações/acordãos cadastradros no sistema através de uma ou mais palavras-chaves.'

    def on_tipo_documento_change(self, tipo_documento=None, **kwargs):
        self.show('tipo_legislacao') if tipo_documento == 'legislacao' else self.hide('tipo_legislacao')


    def has_permission(self):
        return True

    def view(self):
        tipo_legislacao = self.get('tipo_legislacao')
        palavas_chaves = self.get('palavas_chaves')
        criterio_busca = self.get('criterio_busca')
        escopo_busca = self.get('escopo_busca')
        if self.validated_data.get('tipo_documento') == 'legislacao':
            qs = Legislacao.objects
            if tipo_legislacao:
                qs = qs.filter(tipo=tipo_legislacao)
        else:
            qs = Acordao.objects
        resultado = qs.none()
        if criterio_busca == 'toda':
            for campo in escopo_busca:
                resultado = resultado | qs.filter(**{f'{campo}__icontains': palavas_chaves})
        elif criterio_busca == 'qualquer':
            for campo in escopo_busca:
                for palavra in palavas_chaves.split():
                    resultado = resultado | qs.filter(**{f'{campo}__icontains': palavra})
        else:
            for campo in escopo_busca:
                resultado = resultado | qs.filter(**{campo: palavas_chaves})
        return resultado.fields('get_descricao', 'ementa', 'get_arquivo')

class Index(actions.ActionSet):
    actions = Consultar, Totais

    def has_permission(self):
        return True


class RevogarLegislacao(actions.Action):

    class Meta:
        model = Legislacao
        fields = 'revogada_por',
        help_text = 'Serão listadas apenas legislações do mesmo tipo e com data posterior ou igual a data da legislação que está sendo revogada.'

    def get_revogada_por_queryset(self, queryset):
        return queryset.filter(tipo=self.instance.tipo, data__gte=self.instance.data).exclude(pk=self.instance.pk)

    def has_permission(self):
        return self.requires('adm', 'opl')


class DefinirPapeis(actions.Action):
    adm = actions.BooleanField(label='Administrador', initial=False)
    opl = actions.BooleanField(label='Operador de Legislação', initial=False)
    opa = actions.BooleanField(label='Operador de Acordão', initial=False)

    class Meta:
        title = 'Definir Papéis'
        modal = True

    def load(self):
        for name in self.fields:
            self.fields[name].initial = Role.objects.filter(username=self.instance.username, name=name).exists()

    def submit(self):
        for name in self.fields:
            if self.get(name):
                Role.objects.get_or_create(username=self.instance.username, name=name)
            else:
                Role.objects.filter(username=self.instance.username, name=name).delete()

    def has_permission(self):
        return self.requires('adm')