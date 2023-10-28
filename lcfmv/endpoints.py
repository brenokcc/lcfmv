from api import endpoints
from api.components import Boxes, Indicators
from .models import TipoLegislacao, Legislacao, Acordao
from api.models import Role


class AcessoRapido(endpoints.Endpoint):
    def get(self):
        boxes = Boxes(title='Acesso Rápido')
        if self.check_roles('adm'):
            boxes.append(icon='users-line', label='Usuários', url='/api/v1/users/')
        if self.check_roles('adm', 'opl'):
            boxes.append(icon='list', label='Tipos de Legislação', url='/api/v1/tipolegislacao/')
        if self.check_roles('adm'):
            boxes.append(icon='building', label='Conselhos', url='/api/v1/conselho/')
        if self.check_roles('adm', 'opl'):
            boxes.append(icon='file-contract', label='Legislações', url='/api/v1/legislacao/')
        if self.check_roles('adm', 'opa'):
            boxes.append(icon='file-signature', label='Acordãos', url='/api/v1/acordao/')
        return boxes

    def check_permission(self):
        return self.user.is_authenticated


class Totais(endpoints.Endpoint):
    def get(self):
        totais = Indicators('Legislação')
        for tipo in TipoLegislacao.objects.all():
            totais.append(tipo, Legislacao.objects.filter(tipo=tipo).count())
        totais.append('Acordão', Acordao.objects.count())
        return totais

    def check_permission(self):
        return True

class Dashboard(endpoints.EndpointSet):
    endpoints = AcessoRapido, Totais

    def check_permission(self):
        return self.user.is_authenticated


class Consultar(endpoints.Endpoint):
    tipo_documento = endpoints.ChoiceField(
        label='Tipo de Documento', choices=[
            ['legislacao', 'Legislação'],
            ['acordao', 'Acordão'],
        ], pick=True, initial='legislacao'
    )
    tipo_legislacao = endpoints.RelatedField(queryset=TipoLegislacao.objects, label='Tipo de Legislação', required=False, pick=True, help_text='Não informar caso deseje buscar em todos os tipos.')
    palavas_chaves = endpoints.CharField(label='Palavras-chaves', required=True)
    criterio_busca = endpoints.ChoiceField(
        label='Critério da Busca', choices=[
            ['toda', 'Contendo todas palavras'],
            ['qualquer', 'Contendo qualquer uma das palavras'],
            ['exato', 'Cotendo a expressão exata'],
        ], pick=True, initial='toda'
    )
    escopo_busca = endpoints.MultipleChoiceField(
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
        self.enable('tipo_legislacao') if tipo_documento == 'legislacao' else self.disable('tipo_legislacao')
        self.setdata(palavas_chaves='TESTE :)')

    def check_permission(self):
        return True

    def get(self):
        tipo_legislacao = self.getdata('tipo_legislacao')
        palavas_chaves = self.getdata('palavas_chaves')
        criterio_busca = self.getdata('criterio_busca')
        escopo_busca = self.getdata('escopo_busca')
        if self.validated_data.userdata('tipo_documento') == 'legislacao':
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

class Index(endpoints.EndpointSet):
    endpoints = Consultar, Totais

    def check_permission(self):
        return True


class RevogarLegislacao(endpoints.Endpoint):

    class Meta:
        target = 'instance'
        model = Legislacao
        fields = 'revogada_por',
        help_text = 'Serão listadas apenas legislações do mesmo tipo e com data posterior ou igual a data da legislação que está sendo revogada.'

    def get_revogada_por_queryset(self, queryset):
        return queryset.filter(tipo=self.instance.tipo, data__gte=self.instance.data).exclude(pk=self.instance.pk)

    def check_permission(self):
        return self.check_roles('adm', 'opl')


class DefinirPapeis(endpoints.Endpoint):
    adm = endpoints.BooleanField(label='Administrador', initial=False)
    opl = endpoints.BooleanField(label='Operador de Legislação', initial=False)
    opa = endpoints.BooleanField(label='Operador de Acordão', initial=False)

    class Meta:
        title = 'Definir Papéis'
        modal = True
        target = 'instance'

    def load(self):
        for name in self.fields:
            self.fields[name].initial = Role.objects.filter(username=self.instance.username, name=name).exists()

    def post(self):
        for name in self.fields:
            if self.getdata(name):
                Role.objects.get_or_create(username=self.instance.username, name=name)
            else:
                Role.objects.filter(username=self.instance.username, name=name).delete()

    def check_permission(self):
        return self.check_roles('adm')