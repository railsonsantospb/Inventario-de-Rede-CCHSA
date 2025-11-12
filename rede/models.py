from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.html import format_html
from colorfield.fields import ColorField

class Localizacao(models.Model):
    nome = models.CharField('Nome do Local', max_length=100)
    endereco = models.TextField('Endereço')
    observacoes = models.TextField('Observações', blank=True, null=True)
    cor = ColorField('Cor de Identificação', default='#FF0000')
    
    class Meta:
        verbose_name = 'Localização'
        verbose_name_plural = 'Localizações'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome
    
    def colored_name(self):
        return format_html(
            '<span style="color: {};">{}</span>',
            self.cor,
            self.nome
        )
    colored_name.short_description = 'Localização'

class Equipamento(models.Model):
    TIPO_CHOICES = [
        ('SW', 'Switch'),
        ('RT', 'Roteador'),
        ('AP', 'Access Point'),
        ('SR', 'Servidor'),
        ('PC', 'PC Desktop'),
        ('NB', 'Notebook'),
        ('OT', 'Outro')
    ]
    
    nome = models.CharField('Nome do Equipamento', max_length=100)
    tipo = models.CharField('Tipo', max_length=2, choices=TIPO_CHOICES)
    modelo = models.CharField('Modelo', max_length=100)
    marca = models.CharField('Marca', max_length=50)
    numero_serie = models.CharField('Número de Série', max_length=50, blank=True, null=True)
    ip_gerencia = models.GenericIPAddressField('IP de Gerência', protocol='IPv4', blank=True, null=True)
    porta = models.PositiveIntegerField('Porta de Acesso', blank=True, null=True, 
                                      validators=[MinValueValidator(1), MaxValueValidator(65535)],
                                      help_text='Porta de acesso ao equipamento (1-65535)')
    usuario = models.CharField('Usuário', max_length=50, blank=True, null=True)
    senha = models.CharField('Senha', max_length=100, blank=True, null=True)
    localizacao = models.ForeignKey(Localizacao, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='Localização')
    andar = models.CharField('Andar', max_length=50, blank=True, null=True)
    sala = models.CharField('Sala', max_length=50, blank=True, null=True)
    data_instalacao = models.DateField('Data de Instalação', blank=True, null=True)
    garantia_ate = models.DateField('Garantia Até', blank=True, null=True)
    observacoes = models.TextField('Observações', blank=True, null=True)
    ativo = models.BooleanField('Ativo', default=True)
    
    class Meta:
        verbose_name = 'Equipamento'
        verbose_name_plural = 'Equipamentos'
        ordering = ['localizacao', 'tipo', 'nome']
    
    def __str__(self):
        return f"{self.get_tipo_display()} - {self.nome} ({self.localizacao if self.localizacao else 'Sem localização'})"

class PortaSwitch(models.Model):
    equipamento = models.ForeignKey(Equipamento, on_delete=models.CASCADE, related_name='portas', 
                                  limit_choices_to={'tipo__in': ['SW', 'RT']},
                                  verbose_name='Equipamento de Rede')
    numero = models.PositiveIntegerField('Número da Porta', validators=[MinValueValidator(1)])
    descricao = models.CharField('Descrição', max_length=200, blank=True, null=True)
    equipamento_conectado = models.ForeignKey(Equipamento, on_delete=models.SET_NULL, 
                                            null=True, blank=True, related_name='porta_conectada',
                                            verbose_name='Equipamento Conectado',
                                            limit_choices_to={'tipo__in': ['SW', 'RT', 'AP', 'SR', 'PC', 'NB', 'OT']})
    vlan = models.CharField('VLAN', max_length=50, blank=True, null=True)
    VELOCIDADE_CHOICES = [
        ('100M', '100Mbps'),
        ('1G', '1Gbps'),
        ('10G', '10Gbps'),
        ('25G', '25Gbps'),
        ('40G', '40Gbps'),
        ('100G', '100Gbps'),
        ('OUTRA', 'Outra')
    ]
    velocidade = models.CharField(
        'Velocidade',
        max_length=5,
        choices=VELOCIDADE_CHOICES,
        blank=True,
        null=True,
        help_text='Velocidade da porta de rede'
    )
    duplex = models.CharField('Duplex', max_length=20, blank=True, null=True,
                            choices=[('half', 'Half-Duplex'), ('full', 'Full-Duplex')])
    TIPO_CONEXAO_CHOICES = [
        ('', 'Nenhum'),
        ('TX', 'Transmissão (TX) - Fornece internet'),
        ('RX', 'Recepção (RX) - Recebe internet'),
    ]
    tipo_conexao = models.CharField('Tipo de Conexão', max_length=2, 
                                   choices=TIPO_CONEXAO_CHOICES, 
                                   blank=True, null=True,
                                   help_text='Indica se a porta está fornecendo (TX) ou recebendo (RX) internet')
    status = models.BooleanField('Ativa', default=True)
    data_cadastro = models.DateTimeField('Data de Cadastro', auto_now_add=True)
    data_atualizacao = models.DateTimeField('Última Atualização', auto_now=True)
    
    class Meta:
        verbose_name = 'Porta de Equipamento de Rede'
        verbose_name_plural = 'Portas de Equipamentos de Rede'
        ordering = ['equipamento', 'numero']
        unique_together = ['equipamento', 'numero']
    
    def __str__(self):
        return f"{self.equipamento.get_tipo_display()} {self.equipamento.nome} - Porta {self.numero}"

class Manutencao(models.Model):
    TIPO_CHOICES = [
        ('PREV', 'Preventiva'),
        ('CORR', 'Corretiva'),
        ('MELH', 'Melhoria'),
        ('CONF', 'Configuração'),
        ('OUTR', 'Outra')
    ]
    
    equipamento = models.ForeignKey(Equipamento, on_delete=models.CASCADE, related_name='manutencoes')
    tipo = models.CharField('Tipo de Manutenção', max_length=4, choices=TIPO_CHOICES)
    data_hora_inicio = models.DateTimeField('Data/Hora de Início')
    data_hora_fim = models.DateTimeField('Data/Hora de Término', null=True, blank=True)
    descricao = models.TextField('Descrição')
    acoes_realizadas = models.TextField('Ações Realizadas')
    responsavel = models.CharField('Responsável', max_length=100)
    observacoes = models.TextField('Observações', blank=True, null=True)
    
    class Meta:
        verbose_name = 'Manutenção'
        verbose_name_plural = 'Manutenções'
        ordering = ['-data_hora_inicio']
    
    def __str__(self):
        return f"{self.get_tipo_display()} em {self.equipamento} - {self.data_hora_inicio.strftime('%d/%m/%Y %H:%M')}"
