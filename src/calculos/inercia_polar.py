"""
Cálculo da Inércia Polar para componentes de válvulas.

A inércia polar (momento de inércia polar) é necessária para:
- Dimensionamento de atuadores (pneumáticos, elétricos, hidráulicos)
- Cálculo do torque dinâmico durante abertura/fechamento
- Determinação do tempo de operação da válvula

Referências:
- NFPA T3.5.29 - Hydraulic Actuators
- ISA-75.05.01 - Control Valve Terminology
- EN ISO 5211 - Industrial valves - Part-turn actuator attachment
"""

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class TipoValvula(Enum):
    BORBOLETA = "borboleta"
    ESFERA = "esfera"
    GAVETA = "gaveta"
    GLOBO = "globo"
    PLUGUE = "plugue"


class MaterialValvula(Enum):
    """Densidade em kg/m³."""
    ACO_CARBONO = ("Aço Carbono", 7850.0)
    ACO_INOX_304 = ("Aço Inox 304", 7900.0)
    ACO_INOX_316 = ("Aço Inox 316", 8000.0)
    BRONZE = ("Bronze", 8500.0)
    LATAO = ("Latão", 8400.0)
    FERRO_FUNDIDO = ("Ferro Fundido", 7200.0)
    PVC = ("PVC", 1380.0)
    DUPLEX = ("Duplex 2205", 7800.0)

    def __init__(self, descricao: str, densidade: float):
        self.descricao = descricao
        self.densidade = densidade  # kg/m³


@dataclass
class ResultadoInercia:
    tipo_valvula: TipoValvula
    material: MaterialValvula
    diametro_nominal_mm: float
    inercia_polar_kg_m2: float
    massa_kg: float
    torque_dinamico_nm: Optional[float] = None
    aceleracao_angular_rad_s2: Optional[float] = None

    @property
    def inercia_polar_g_cm2(self) -> float:
        """Converte kg·m² para g·cm² (unidade comum em catálogos)."""
        return self.inercia_polar_kg_m2 * 1e7

    def __str__(self) -> str:
        lines = [
            f"Válvula {self.tipo_valvula.value.title()} - DN{self.diametro_nominal_mm:.0f}",
            f"  Material         : {self.material.descricao}",
            f"  Massa            : {self.massa_kg:.4f} kg",
            f"  Inércia Polar    : {self.inercia_polar_kg_m2:.6f} kg·m²",
            f"  Inércia Polar    : {self.inercia_polar_g_cm2:.2f} g·cm²",
        ]
        if self.torque_dinamico_nm is not None:
            lines.append(
                f"  Torque Dinâmico  : {self.torque_dinamico_nm:.4f} N·m"
                f" (α = {self.aceleracao_angular_rad_s2:.2f} rad/s²)"
            )
        return "\n".join(lines)


class InerciaPolar:
    """
    Calcula a inércia polar de componentes rotativos de válvulas.

    A inércia polar é calculada em relação ao eixo de rotação da haste (stem),
    pois é esse eixo que determina o torque necessário no atuador.
    """

    @staticmethod
    def disco_solido(
        raio_m: float,
        espessura_m: float,
        material: MaterialValvula,
    ) -> tuple[float, float]:
        """
        Disco sólido rotacionando em torno do seu eixo central (válvula borboleta).

        Ip = (1/2) * m * r²

        Args:
            raio_m: Raio do disco em metros
            espessura_m: Espessura do disco em metros
            material: Material do disco

        Returns:
            Tupla (inercia_polar_kg_m2, massa_kg)
        """
        volume = math.pi * raio_m**2 * espessura_m
        massa = material.densidade * volume
        inercia = 0.5 * massa * raio_m**2
        return inercia, massa

    @staticmethod
    def disco_oco(
        raio_externo_m: float,
        raio_interno_m: float,
        espessura_m: float,
        material: MaterialValvula,
    ) -> tuple[float, float]:
        """
        Disco anelar (anel) rotacionando em torno do seu eixo central.

        Ip = (1/2) * m * (r_ext² + r_int²)

        Args:
            raio_externo_m: Raio externo em metros
            raio_interno_m: Raio interno (furo) em metros
            espessura_m: Espessura em metros
            material: Material

        Returns:
            Tupla (inercia_polar_kg_m2, massa_kg)
        """
        volume = math.pi * (raio_externo_m**2 - raio_interno_m**2) * espessura_m
        massa = material.densidade * volume
        inercia = 0.5 * massa * (raio_externo_m**2 + raio_interno_m**2)
        return inercia, massa

    @staticmethod
    def esfera_solida(
        raio_m: float,
        material: MaterialValvula,
    ) -> tuple[float, float]:
        """
        Esfera sólida (válvula de esfera - ball valve).

        Ip = (2/5) * m * r²

        Args:
            raio_m: Raio da esfera em metros
            material: Material da esfera

        Returns:
            Tupla (inercia_polar_kg_m2, massa_kg)
        """
        volume = (4 / 3) * math.pi * raio_m**3
        massa = material.densidade * volume
        inercia = (2 / 5) * massa * raio_m**2
        return inercia, massa

    @staticmethod
    def esfera_com_furo(
        raio_m: float,
        raio_furo_m: float,
        material: MaterialValvula,
    ) -> tuple[float, float]:
        """
        Esfera com furo passante (ball valve com orifício).

        Calculado por subtração de volumes: esfera sólida menos cilindro do furo.
        A inércia do furo é subtraída via teorema de Steiner se necessário,
        mas para furo central o eixo coincide.

        Args:
            raio_m: Raio da esfera em metros
            raio_furo_m: Raio do furo passante em metros
            material: Material

        Returns:
            Tupla (inercia_polar_kg_m2, massa_kg)
        """
        comprimento_furo = 2 * raio_m
        volume_esfera = (4 / 3) * math.pi * raio_m**3
        volume_furo = math.pi * raio_furo_m**2 * comprimento_furo
        volume = volume_esfera - volume_furo
        massa = material.densidade * volume

        # Inércia da esfera sólida menos inércia do cilindro removido
        massa_esfera = material.densidade * volume_esfera
        massa_furo = material.densidade * volume_furo
        ip_esfera = (2 / 5) * massa_esfera * raio_m**2
        ip_furo = 0.5 * massa_furo * raio_furo_m**2
        inercia = ip_esfera - ip_furo
        return inercia, massa

    @staticmethod
    def cilindro_solido(
        raio_m: float,
        comprimento_m: float,
        material: MaterialValvula,
    ) -> tuple[float, float]:
        """
        Cilindro sólido (haste/stem, plugue cilíndrico).

        Ip = (1/2) * m * r²

        Args:
            raio_m: Raio do cilindro em metros
            comprimento_m: Comprimento (altura) em metros
            material: Material

        Returns:
            Tupla (inercia_polar_kg_m2, massa_kg)
        """
        volume = math.pi * raio_m**2 * comprimento_m
        massa = material.densidade * volume
        inercia = 0.5 * massa * raio_m**2
        return inercia, massa

    @staticmethod
    def placa_retangular(
        largura_m: float,
        altura_m: float,
        espessura_m: float,
        material: MaterialValvula,
    ) -> tuple[float, float]:
        """
        Placa retangular rotacionando em torno do eixo perpendicular ao plano (gaveta/gate).

        Ip = (1/12) * m * (a² + b²)

        onde a = largura e b = altura da placa.

        Args:
            largura_m: Largura da placa em metros
            altura_m: Altura da placa em metros
            espessura_m: Espessura da placa em metros
            material: Material

        Returns:
            Tupla (inercia_polar_kg_m2, massa_kg)
        """
        volume = largura_m * altura_m * espessura_m
        massa = material.densidade * volume
        inercia = (1 / 12) * massa * (largura_m**2 + altura_m**2)
        return inercia, massa

    @classmethod
    def valvula_borboleta(
        cls,
        diametro_nominal_mm: float,
        material: MaterialValvula = MaterialValvula.ACO_INOX_316,
        fator_espessura: float = 0.12,
        aceleracao_angular_rad_s2: Optional[float] = None,
    ) -> ResultadoInercia:
        """
        Inércia polar do disco de uma válvula borboleta (butterfly valve).

        O disco é modelado como um disco sólido. A espessura é estimada como
        uma fração do diâmetro nominal (fator_espessura).

        Args:
            diametro_nominal_mm: DN em milímetros (ex: 50, 100, 200, 300)
            material: Material do disco
            fator_espessura: Relação espessura/diâmetro (padrão 0.12 para aço)
            aceleracao_angular_rad_s2: Se fornecido, calcula torque dinâmico (rad/s²)

        Returns:
            ResultadoInercia com todos os dados calculados
        """
        raio = (diametro_nominal_mm / 2) / 1000  # m
        espessura = diametro_nominal_mm * fator_espessura / 1000  # m

        inercia, massa = cls.disco_solido(raio, espessura, material)

        torque = None
        if aceleracao_angular_rad_s2 is not None:
            torque = inercia * aceleracao_angular_rad_s2

        return ResultadoInercia(
            tipo_valvula=TipoValvula.BORBOLETA,
            material=material,
            diametro_nominal_mm=diametro_nominal_mm,
            inercia_polar_kg_m2=inercia,
            massa_kg=massa,
            torque_dinamico_nm=torque,
            aceleracao_angular_rad_s2=aceleracao_angular_rad_s2,
        )

    @classmethod
    def valvula_esfera(
        cls,
        diametro_nominal_mm: float,
        material: MaterialValvula = MaterialValvula.ACO_INOX_316,
        fator_furo: float = 0.8,
        aceleracao_angular_rad_s2: Optional[float] = None,
    ) -> ResultadoInercia:
        """
        Inércia polar da esfera de uma válvula de esfera (ball valve).

        A esfera é modelada com furo passante cujo diâmetro é fator_furo * DN.

        Args:
            diametro_nominal_mm: DN em milímetros
            material: Material da esfera
            fator_furo: Relação diâmetro_furo/DN (full bore ≈ 1.0, reduced ≈ 0.7)
            aceleracao_angular_rad_s2: Se fornecido, calcula torque dinâmico

        Returns:
            ResultadoInercia
        """
        # Diâmetro da esfera é tipicamente 1.2× o DN
        raio_esfera = (diametro_nominal_mm * 1.2 / 2) / 1000  # m
        raio_furo = (diametro_nominal_mm * fator_furo / 2) / 1000  # m

        inercia, massa = cls.esfera_com_furo(raio_esfera, raio_furo, material)

        torque = None
        if aceleracao_angular_rad_s2 is not None:
            torque = inercia * aceleracao_angular_rad_s2

        return ResultadoInercia(
            tipo_valvula=TipoValvula.ESFERA,
            material=material,
            diametro_nominal_mm=diametro_nominal_mm,
            inercia_polar_kg_m2=inercia,
            massa_kg=massa,
            torque_dinamico_nm=torque,
            aceleracao_angular_rad_s2=aceleracao_angular_rad_s2,
        )

    @classmethod
    def valvula_plugue(
        cls,
        diametro_nominal_mm: float,
        material: MaterialValvula = MaterialValvula.ACO_INOX_316,
        aceleracao_angular_rad_s2: Optional[float] = None,
    ) -> ResultadoInercia:
        """
        Inércia polar do plugue de uma válvula de plugue (plug valve).

        O plugue é modelado como um cilindro sólido com altura igual ao DN.

        Args:
            diametro_nominal_mm: DN em milímetros
            material: Material do plugue
            aceleracao_angular_rad_s2: Se fornecido, calcula torque dinâmico

        Returns:
            ResultadoInercia
        """
        raio = (diametro_nominal_mm / 2) / 1000  # m
        comprimento = diametro_nominal_mm / 1000  # m

        inercia, massa = cls.cilindro_solido(raio, comprimento, material)

        torque = None
        if aceleracao_angular_rad_s2 is not None:
            torque = inercia * aceleracao_angular_rad_s2

        return ResultadoInercia(
            tipo_valvula=TipoValvula.PLUGUE,
            material=material,
            diametro_nominal_mm=diametro_nominal_mm,
            inercia_polar_kg_m2=inercia,
            massa_kg=massa,
            torque_dinamico_nm=torque,
            aceleracao_angular_rad_s2=aceleracao_angular_rad_s2,
        )

    @staticmethod
    def tempo_para_aceleracao(
        inercia_polar_kg_m2: float,
        torque_disponivel_nm: float,
        angulo_rotacao_graus: float = 90.0,
    ) -> float:
        """
        Estima o tempo mínimo de operação para uma válvula de quarto de volta.

        Assume aceleração constante até metade do curso e desaceleração na outra metade.
        t = 2 * sqrt(θ / α)  onde  α = T / Ip

        Args:
            inercia_polar_kg_m2: Inércia polar em kg·m²
            torque_disponivel_nm: Torque do atuador em N·m
            angulo_rotacao_graus: Ângulo total de rotação (padrão 90°)

        Returns:
            Tempo mínimo de operação em segundos
        """
        if torque_disponivel_nm <= 0:
            raise ValueError("Torque disponível deve ser positivo.")

        angulo_rad = math.radians(angulo_rotacao_graus)
        aceleracao = torque_disponivel_nm / inercia_polar_kg_m2
        # Equação cinemática: θ/2 = (1/2) * α * (t/2)²  →  t = 2 * sqrt(θ/α)
        tempo = 2 * math.sqrt(angulo_rad / aceleracao)
        return tempo

    @staticmethod
    def aceleracao_angular_de_tempo(
        inercia_polar_kg_m2: float,
        tempo_operacao_s: float,
        angulo_rotacao_graus: float = 90.0,
    ) -> dict:
        """
        Calcula a aceleração angular e o torque dinâmico mínimo necessário
        para operar a válvula no tempo especificado.

        Args:
            inercia_polar_kg_m2: Inércia polar em kg·m²
            tempo_operacao_s: Tempo de operação desejado em segundos
            angulo_rotacao_graus: Ângulo total de rotação

        Returns:
            Dicionário com aceleracao_rad_s2 e torque_dinamico_nm
        """
        angulo_rad = math.radians(angulo_rotacao_graus)
        # t = 2 * sqrt(θ/α)  →  α = 4θ / t²
        aceleracao = 4 * angulo_rad / tempo_operacao_s**2
        torque = inercia_polar_kg_m2 * aceleracao
        return {
            "aceleracao_rad_s2": aceleracao,
            "torque_dinamico_nm": torque,
        }
