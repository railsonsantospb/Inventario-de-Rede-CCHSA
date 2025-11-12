from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.http import JsonResponse
from django.utils.safestring import mark_safe
from django.contrib import messages
from django import forms
from django.db.models import Q
from .models import Localizacao, Equipamento, PortaSwitch, Manutencao

@admin.register(Localizacao)
class LocalizacaoAdmin(admin.ModelAdmin):
    list_display = ('colored_name', 'endereco_curto', 'qtd_equipamentos')
    list_filter = ('nome',)
    search_fields = ('nome', 'endereco')
    readonly_fields = ('cor_preview',)
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('nome', 'endereco', 'observacoes')
        }),
        ('Identificação Visual', {
            'fields': ('cor', 'cor_preview')
        }),
    )
    
    def cor_preview(self, obj):
        if obj.cor:
            return format_html(
                '<div style="width: 50px; height: 20px; background-color: {};"></div>',
                obj.cor
            )
        return "-"
    cor_preview.short_description = 'Visualização da Cor'
    
    def endereco_curto(self, obj):
        return f"{obj.endereco[:50]}..." if obj.endereco else ""
    endereco_curto.short_description = 'Endereço'
    
    def qtd_equipamentos(self, obj):
        count = obj.equipamento_set.count()
        url = f"{reverse('admin:rede_equipamento_changelist')}?localizacao__id__exact={obj.id}"
        return format_html('<a href="{}">{} equipamentos</a>', url, count)
    qtd_equipamentos.short_description = 'Equipamentos'

class PortaSwitchInline(admin.TabularInline):
    model = PortaSwitch
    extra = 0
    fields = ('numero', 'descricao', 'equipamento_conectado', 'vlan', 'status')
    readonly_fields = ('data_cadastro', 'data_atualizacao')
    show_change_link = True
    fk_name = 'equipamento'

@admin.register(Equipamento)
class EquipamentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'tipo_display', 'modelo', 'localizacao_link', 'ip_gerencia', 'ativo')
    list_filter = ('tipo', 'localizacao', 'ativo')
    search_fields = ('nome', 'modelo', 'marca', 'numero_serie', 'ip_gerencia')
    list_editable = ('ativo',)
    inlines = [PortaSwitchInline]
    fieldsets = (
        ('Identificação', {
            'fields': ('nome', 'tipo', 'modelo', 'marca', 'numero_serie', 'ativo')
        }),
        ('Conexão', {
            'fields': ('ip_gerencia', 'porta', 'usuario', 'senha')
        }),
        ('Localização', {
            'fields': ('localizacao', 'andar', 'sala')
        }),
        ('Datas Importantes', {
            'fields': ('data_instalacao', 'garantia_ate'),
            'classes': ('collapse',)
        }),
        ('Outras Informações', {
            'fields': ('observacoes',),
            'classes': ('collapse',)
        }),
    )
    
    def tipo_display(self, obj):
        return obj.get_tipo_display()
    tipo_display.short_description = 'Tipo'
    
    def localizacao_link(self, obj):
        if obj.localizacao:
            url = reverse('admin:rede_localizacao_change', args=[obj.localizacao.id])
            return format_html('<a href="{}">{}</a>', url, obj.localizacao)
        return "-"
    localizacao_link.short_description = 'Localização'
    localizacao_link.admin_order_field = 'localizacao__nome'

class PortaSwitchForm(forms.ModelForm):
    class Meta:
        model = PortaSwitch
        fields = '__all__'

class EquipamentoConectadoFilter(admin.SimpleListFilter):
    title = 'equipamento conectado (roteadores e switches)'
    parameter_name = 'equipamento_conectado'

    def lookups(self, request, model_admin):
        # Filtra apenas equipamentos do tipo Roteador (RT) ou Switch (SW) que estão conectados
        equipamentos = Equipamento.objects.filter(
            id__in=PortaSwitch.objects.exclude(equipamento_conectado__isnull=True)
                                     .values_list('equipamento_conectado', flat=True),
            tipo__in=['RT', 'SW']  # Apenas roteadores e switches
        ).distinct()
        return [(e.id, f"{e.get_tipo_display()} - {e.nome}") for e in equipamentos]

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(equipamento_conectado__id__exact=self.value())
        return queryset


class LocalizacaoFilter(admin.SimpleListFilter):
    title = 'localização do equipamento conectado'
    parameter_name = 'localizacao_equipamento_conectado'

    def lookups(self, request, model_admin):
        # Retorna uma lista de tuplas (valor, rótulo) com localizações de equipamentos conectados
        localizacoes = Localizacao.objects.filter(
            equipamento__porta_conectada__isnull=False
        ).distinct().values_list('id', 'nome').order_by('nome')
        return localizacoes

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(equipamento_conectado__localizacao_id=self.value())
        return queryset

@admin.register(PortaSwitch)
class PortaSwitchAdmin(admin.ModelAdmin):
    form = PortaSwitchForm
    list_display = ('__str__', 'equipamento_link', 'equipamento_conectado_link', 'vlan', 'status', 'tipo_conexao_display')
    list_filter = ('equipamento', EquipamentoConectadoFilter, 'status', 'vlan', 'tipo_conexao', LocalizacaoFilter)
    search_fields = ('equipamento__nome', 'descricao', 'equipamento_conectado__nome')
    list_editable = ('status', 'vlan')
    readonly_fields = ('data_cadastro', 'data_atualizacao')
    
    class Media:
        js = ('admin/js/portaswitch_filter.js',)
    
    def tipo_conexao_display(self, obj):
        return dict(PortaSwitch.TIPO_CONEXAO_CHOICES).get(obj.tipo_conexao, '-')
    tipo_conexao_display.short_description = 'Tipo de Conexão'
    
    def equipamento_link(self, obj):
        url = reverse('admin:rede_equipamento_change', args=[obj.equipamento.id])
        return format_html('<a href="{}">{}</a>', url, obj.equipamento)
    equipamento_link.short_description = 'Equipamento de Rede'
    equipamento_link.admin_order_field = 'equipamento__nome'
    
    def equipamento_conectado_link(self, obj):
        if obj.equipamento_conectado:
            url = reverse('admin:rede_equipamento_change', args=[obj.equipamento_conectado.id])
            return format_html('<a href="{}">{}</a>', url, obj.equipamento_conectado)
        return "-"
    equipamento_conectado_link.short_description = 'Equipamento Conectado'

@admin.register(Manutencao)
class ManutencaoAdmin(admin.ModelAdmin):
    list_display = ('data_hora_inicio', 'equipamento_link', 'tipo_display', 'responsavel', 'duracao')
    list_filter = ('tipo', 'equipamento', 'responsavel')
    search_fields = ('equipamento__nome', 'descricao', 'acoes_realizadas', 'responsavel')
    date_hierarchy = 'data_hora_inicio'
    
    def tipo_display(self, obj):
        return obj.get_tipo_display()
    tipo_display.short_description = 'Tipo'
    
    def equipamento_link(self, obj):
        url = reverse('admin:rede_equipamento_change', args=[obj.equipamento.id])
        return format_html('<a href="{}">{}</a>', url, obj.equipamento)
    equipamento_link.short_description = 'Equipamento'
    equipamento_link.admin_order_field = 'equipamento__nome'
    
    def duracao(self, obj):
        if obj.data_hora_fim:
            delta = obj.data_hora_fim - obj.data_hora_inicio
            hours, remainder = divmod(delta.seconds, 3600)
            minutes, _ = divmod(remainder, 60)
            return f"{hours}h {minutes}m"
        return "Em andamento"
    duracao.short_description = 'Duração'
