"""
Cálculo do Momento de Inércia Polar para conjunto moto-bomba.

Baseado em:
- Castro, M.A.H. - Momento de Inércia - Aula UFC (seção 5.1 - Conjunto Moto-bomba)

Métodos disponíveis:
1. Geométrico (cilindro maciço ou oco) via diâmetro de giração / GD²
2. Empírico - Koelle e Betâmio (1992): I = 288·(P/N0)^1,435
3. Empírico - Thorley e Faithfull (1992): I = I1 + I2 (rotor/fluido + motor)

Referências:
- Koelle, E.; Betâmio, A. (1992)
- Thorley, A.R.D.; Faithfull, E.M. (1992)
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Optional


class MetodoCalculo(Enum):
    GEOMETRICO_MACICO = "geometrico_macico"
    GEOMETRICO_OCO = "geometrico_oco"
    KOELLE_BETAMIO = "koelle_betamio"
    THORLEY_FAITHFULL = "thorley_faithfull"


@dataclass
class ResultadoInerciaBomba:
    metodo: MetodoCalculo
    inercia_total_kg_m2: float
    inercia_rotor_fluido_kg_m2: Optional[float] = None  # I1 (Thorley-Faithfull)
    inercia_motor_kg_m2: Optional[float] = None          # I2 (Thorley-Faithfull)
    momento_impulsao_gd2: Optional[float] = None          # GD² em kg·m²
    massa_kg: Optional[float] = None
    potencia_kw: Optional[float] = None
    rotacao_rpm: Optional[float] = None

    def __str__(self) -> str:
        metodo_label = self.metodo.value.replace("_", " ").title()
        lines = [
            f"Método : {metodo_label}",
            f"  Inércia Polar Total   : {self.inercia_total_kg_m2:.6f} kg·m²",
        ]
        if self.inercia_rotor_fluido_kg_m2 is not None:
            lines.append(
                f"  Inércia I1 (rotor+fl) : {self.inercia_rotor_fluido_kg_m2:.6f} kg·m²"
            )
        if self.inercia_motor_kg_m2 is not None:
            lines.append(
                f"  Inércia I2 (motor)    : {self.inercia_motor_kg_m2:.6f} kg·m²"
            )
        if self.momento_impulsao_gd2 is not None:
            lines.append(
                f"  Momento de Impulsão   : {self.momento_impulsao_gd2:.6f} kg·m²  (GD²)"
            )
        if self.massa_kg is not None:
            lines.append(f"  Massa                 : {self.massa_kg:.4f} kg")
        if self.potencia_kw is not None:
            lines.append(f"  Potência              : {self.potencia_kw:.2f} kW")
        if self.rotacao_rpm is not None:
            lines.append(f"  Rotação               : {self.rotacao_rpm:.0f} rpm")
        return "\n".join(lines)


class InerciaMotoBomba:
    """
    Calcula o momento de inércia polar do conjunto moto-bomba.

    Referência: Castro, M.A.H. (UFC) - seção 5.1.1 Momento de Inércia.
    """

    G_GRAVIDADE = 9.81  # m/s²

    @classmethod
    def cilindro_macico(
        cls,
        massa_kg: float,
        diametro_m: float,
    ) -> ResultadoInerciaBomba:
        """
        Inércia polar geométrica — cilindro maciço.

        Diâmetro de giração: D² = d²/2
        Momento de inércia:  I = m·r²/2  (equivalente a G·D²/4, G em kgf)
        Momento de impulsão: GD² = m·D²

        Args:
            massa_kg: Massa do rotor em kg (ou peso em kgf, numericamente igual)
            diametro_m: Diâmetro do cilindro em metros

        Returns:
            ResultadoInerciaBomba com I e GD²
        """
        if massa_kg <= 0:
            raise ValueError("Massa deve ser positiva.")
        if diametro_m <= 0:
            raise ValueError("Diâmetro deve ser positivo.")

        # D² de giração = d²/2  (Eq. 5.5)
        D2 = diametro_m**2 / 2
        # I = m·D²/4  (Eq. 5.4 com G em kgf)  — igual a m·r²/2
        inercia = massa_kg * D2 / 4
        gd2 = massa_kg * D2  # GD² em kg·m²

        return ResultadoInerciaBomba(
            metodo=MetodoCalculo.GEOMETRICO_MACICO,
            inercia_total_kg_m2=inercia,
            momento_impulsao_gd2=gd2,
            massa_kg=massa_kg,
        )

    @classmethod
    def cilindro_oco(
        cls,
        massa_kg: float,
        diametro_interno_m: float,
        diametro_externo_m: float,
    ) -> ResultadoInerciaBomba:
        """
        Inércia polar geométrica — cilindro oco (anel).

        Diâmetro de giração: D² = (d1² + d2²)/2  (Eq. 5.6)
        Momento de inércia:  I = m·(r1² + r2²)/2  (Eq. 5.7)
        Momento de impulsão: GD² = m·D²

        Args:
            massa_kg: Massa do rotor em kg
            diametro_interno_m: Diâmetro interno em metros
            diametro_externo_m: Diâmetro externo em metros

        Returns:
            ResultadoInerciaBomba com I e GD²
        """
        if massa_kg <= 0:
            raise ValueError("Massa deve ser positiva.")
        if diametro_interno_m <= 0 or diametro_externo_m <= 0:
            raise ValueError("Diâmetros devem ser positivos.")
        if diametro_interno_m >= diametro_externo_m:
            raise ValueError("Diâmetro interno deve ser menor que o externo.")

        r1 = diametro_interno_m / 2
        r2 = diametro_externo_m / 2
        # D² de giração = (d1² + d2²)/2  (Eq. 5.6)
        D2 = (diametro_interno_m**2 + diametro_externo_m**2) / 2
        # I = m·(r1² + r2²)/2  (Eq. 5.7)
        inercia = massa_kg * (r1**2 + r2**2) / 2
        gd2 = massa_kg * D2  # GD² em kg·m²

        return ResultadoInerciaBomba(
            metodo=MetodoCalculo.GEOMETRICO_OCO,
            inercia_total_kg_m2=inercia,
            momento_impulsao_gd2=gd2,
            massa_kg=massa_kg,
        )

    @classmethod
    def koelle_betamio(
        cls,
        potencia_hp: float,
        rotacao_rpm: float,
    ) -> ResultadoInerciaBomba:
        """
        Inércia polar pelo método empírico de Koelle e Betâmio (1992).

        Equação (5.8): I = 288 · (P / N0)^1,435
        ATENÇÃO: não usar para bombas multiestágio.

        Args:
            potencia_hp: Potência da bomba em HP
            rotacao_rpm: Rotação em rpm (estado permanente)

        Returns:
            ResultadoInerciaBomba
        """
        if potencia_hp <= 0:
            raise ValueError("Potência deve ser positiva.")
        if rotacao_rpm <= 0:
            raise ValueError("Rotação deve ser positiva.")

        inercia = 288.0 * (potencia_hp / rotacao_rpm) ** 1.435
        potencia_kw = potencia_hp * 0.7457  # HP → kW

        return ResultadoInerciaBomba(
            metodo=MetodoCalculo.KOELLE_BETAMIO,
            inercia_total_kg_m2=inercia,
            potencia_kw=potencia_kw,
            rotacao_rpm=rotacao_rpm,
        )

    @classmethod
    def thorley_faithfull(
        cls,
        potencia_kw: float,
        rotacao_rpm: float,
    ) -> ResultadoInerciaBomba:
        """
        Inércia polar pelo método de Thorley e Faithfull (1992).

        Equações (5.9) e (5.10):
          I1 = 0,038 · [P / (N0/1000)³]^0,96   (rotor + fluido)
          I2 = 0,0043 · [P / (N0/1000)]^1,48    (motor)
          I  = I1 + I2

        ATENÇÃO: não usar para bombas multiestágio.

        Args:
            potencia_kw: Potência do conjunto em kW (estado permanente)
            rotacao_rpm: Rotação em rpm (estado permanente)

        Returns:
            ResultadoInerciaBomba com I1, I2 e I total
        """
        if potencia_kw <= 0:
            raise ValueError("Potência deve ser positiva.")
        if rotacao_rpm <= 0:
            raise ValueError("Rotação deve ser positiva.")

        n = rotacao_rpm / 1000.0  # N0/1000

        i1 = 0.038 * (potencia_kw / n**3) ** 0.96   # Eq. 5.9
        i2 = 0.0043 * (potencia_kw / n) ** 1.48      # Eq. 5.10

        return ResultadoInerciaBomba(
            metodo=MetodoCalculo.THORLEY_FAITHFULL,
            inercia_total_kg_m2=i1 + i2,
            inercia_rotor_fluido_kg_m2=i1,
            inercia_motor_kg_m2=i2,
            potencia_kw=potencia_kw,
            rotacao_rpm=rotacao_rpm,
        )

    @staticmethod
    def energia_cinetica(
        inercia_kg_m2: float,
        rotacao_rpm: float,
    ) -> float:
        """
        Energia cinética acumulada no conjunto girante.

        Ec = I · ω² / 2  (Eq. 5.2)

        Args:
            inercia_kg_m2: Momento de inércia em kg·m²
            rotacao_rpm: Rotação em rpm

        Returns:
            Energia cinética em joules
        """
        omega = rotacao_rpm * 2 * math.pi / 60  # rad/s
        return 0.5 * inercia_kg_m2 * omega**2

    @staticmethod
    def gd2_para_inercia(gd2_kg_m2: float) -> float:
        """
        Converte GD² (kg·m²) para momento de inércia I (kg·m²).

        I = GD² / 4  (Eq. 5.4)

        Args:
            gd2_kg_m2: Momento de impulsão GD² em kg·m²

        Returns:
            Momento de inércia I em kg·m²
        """
        if gd2_kg_m2 < 0:
            raise ValueError("GD² deve ser não-negativo.")
        return gd2_kg_m2 / 4.0

    @staticmethod
    def inercia_para_gd2(inercia_kg_m2: float) -> float:
        """
        Converte momento de inércia I (kg·m²) para GD² (kg·m²).

        GD² = 4 · I

        Args:
            inercia_kg_m2: Momento de inércia em kg·m²

        Returns:
            GD² em kg·m²
        """
        if inercia_kg_m2 < 0:
            raise ValueError("Inércia deve ser não-negativa.")
        return 4.0 * inercia_kg_m2
