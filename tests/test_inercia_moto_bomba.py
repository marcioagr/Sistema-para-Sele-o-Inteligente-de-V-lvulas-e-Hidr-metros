"""Testes unitários para o módulo de cálculo da inércia polar do conjunto moto-bomba."""

import math
import pytest
from src.calculos.inercia_moto_bomba import (
    InerciaMotoBomba,
    MetodoCalculo,
    ResultadoInerciaBomba,
)


class TestCilindroMacico:
    def test_exemplo_da_aula(self):
        # Exemplo do PDF: G = 60 N → m = 60/9,81 ≈ 6,116 kg, d = 0,10 m
        # Resultado esperado: I ≈ 7,64 × 10⁻³ kg·m²
        massa = 60 / 9.81
        res = InerciaMotoBomba.cilindro_macico(massa_kg=massa, diametro_m=0.10)
        assert math.isclose(res.inercia_total_kg_m2, 7.645e-3, rel_tol=1e-3)

    def test_formula_equivale_a_mr2_sobre_2(self):
        m, d = 10.0, 0.20
        r = d / 2
        esperado = m * r**2 / 2
        res = InerciaMotoBomba.cilindro_macico(massa_kg=m, diametro_m=d)
        assert math.isclose(res.inercia_total_kg_m2, esperado, rel_tol=1e-9)

    def test_gd2_igual_a_4_vezes_inercia(self):
        res = InerciaMotoBomba.cilindro_macico(massa_kg=5.0, diametro_m=0.15)
        assert math.isclose(res.momento_impulsao_gd2, 4 * res.inercia_total_kg_m2, rel_tol=1e-9)

    def test_metodo_enum_correto(self):
        res = InerciaMotoBomba.cilindro_macico(1.0, 0.1)
        assert res.metodo == MetodoCalculo.GEOMETRICO_MACICO

    def test_massa_invalida(self):
        with pytest.raises(ValueError):
            InerciaMotoBomba.cilindro_macico(massa_kg=0.0, diametro_m=0.1)

    def test_diametro_invalido(self):
        with pytest.raises(ValueError):
            InerciaMotoBomba.cilindro_macico(massa_kg=5.0, diametro_m=0.0)

    def test_inercia_cresce_com_diametro(self):
        r1 = InerciaMotoBomba.cilindro_macico(10.0, 0.10)
        r2 = InerciaMotoBomba.cilindro_macico(10.0, 0.20)
        # Para mesma massa, I ∝ d² → duplicar d quadruplica I
        assert math.isclose(r2.inercia_total_kg_m2 / r1.inercia_total_kg_m2, 4.0, rel_tol=1e-9)


class TestCilindroOco:
    def test_formula_basica(self):
        m, d1, d2 = 8.0, 0.05, 0.15
        r1, r2 = d1 / 2, d2 / 2
        esperado = m * (r1**2 + r2**2) / 2
        res = InerciaMotoBomba.cilindro_oco(m, d1, d2)
        assert math.isclose(res.inercia_total_kg_m2, esperado, rel_tol=1e-9)

    def test_gd2_igual_a_4_vezes_inercia(self):
        res = InerciaMotoBomba.cilindro_oco(6.0, 0.04, 0.12)
        assert math.isclose(res.momento_impulsao_gd2, 4 * res.inercia_total_kg_m2, rel_tol=1e-9)

    def test_metodo_enum_correto(self):
        res = InerciaMotoBomba.cilindro_oco(5.0, 0.02, 0.10)
        assert res.metodo == MetodoCalculo.GEOMETRICO_OCO

    def test_oco_maior_que_macico_mesma_massa_mesmo_d_externo(self):
        # Cilindro oco com mesmo d_externo e mesma massa tem I maior que maciço
        # pois massa está distribuída mais longe do eixo
        m, d_ext = 10.0, 0.20
        macico = InerciaMotoBomba.cilindro_macico(m, d_ext)
        oco = InerciaMotoBomba.cilindro_oco(m, 0.10, d_ext)
        assert oco.inercia_total_kg_m2 > macico.inercia_total_kg_m2

    def test_diametros_invalidos(self):
        with pytest.raises(ValueError):
            InerciaMotoBomba.cilindro_oco(5.0, 0.15, 0.10)  # interno > externo

    def test_massa_invalida(self):
        with pytest.raises(ValueError):
            InerciaMotoBomba.cilindro_oco(-1.0, 0.05, 0.10)


class TestKoelleBetamio:
    def test_resultado_positivo(self):
        res = InerciaMotoBomba.koelle_betamio(potencia_hp=50.0, rotacao_rpm=1750.0)
        assert res.inercia_total_kg_m2 > 0

    def test_metodo_enum_correto(self):
        res = InerciaMotoBomba.koelle_betamio(100.0, 1750.0)
        assert res.metodo == MetodoCalculo.KOELLE_BETAMIO

    def test_potencia_maior_aumenta_inercia(self):
        r1 = InerciaMotoBomba.koelle_betamio(50.0, 1750.0)
        r2 = InerciaMotoBomba.koelle_betamio(100.0, 1750.0)
        assert r2.inercia_total_kg_m2 > r1.inercia_total_kg_m2

    def test_rotacao_maior_diminui_inercia(self):
        r1 = InerciaMotoBomba.koelle_betamio(100.0, 1750.0)
        r2 = InerciaMotoBomba.koelle_betamio(100.0, 3500.0)
        assert r2.inercia_total_kg_m2 < r1.inercia_total_kg_m2

    def test_conversao_hp_para_kw(self):
        res = InerciaMotoBomba.koelle_betamio(100.0, 1750.0)
        assert math.isclose(res.potencia_kw, 100.0 * 0.7457, rel_tol=1e-9)

    def test_potencia_invalida(self):
        with pytest.raises(ValueError):
            InerciaMotoBomba.koelle_betamio(0.0, 1750.0)

    def test_rotacao_invalida(self):
        with pytest.raises(ValueError):
            InerciaMotoBomba.koelle_betamio(50.0, 0.0)


class TestThorleyFaithfull:
    def test_resultado_positivo(self):
        res = InerciaMotoBomba.thorley_faithfull(potencia_kw=21.0, rotacao_rpm=1450.0)
        assert res.inercia_total_kg_m2 > 0

    def test_metodo_enum_correto(self):
        res = InerciaMotoBomba.thorley_faithfull(21.0, 1450.0)
        assert res.metodo == MetodoCalculo.THORLEY_FAITHFULL

    def test_soma_i1_mais_i2(self):
        res = InerciaMotoBomba.thorley_faithfull(21.0, 1450.0)
        soma = res.inercia_rotor_fluido_kg_m2 + res.inercia_motor_kg_m2
        assert math.isclose(res.inercia_total_kg_m2, soma, rel_tol=1e-9)

    def test_i1_e_i2_presentes(self):
        res = InerciaMotoBomba.thorley_faithfull(50.0, 1750.0)
        assert res.inercia_rotor_fluido_kg_m2 is not None
        assert res.inercia_motor_kg_m2 is not None

    def test_potencia_maior_aumenta_inercia(self):
        r1 = InerciaMotoBomba.thorley_faithfull(21.0, 1450.0)
        r2 = InerciaMotoBomba.thorley_faithfull(50.0, 1450.0)
        assert r2.inercia_total_kg_m2 > r1.inercia_total_kg_m2

    def test_potencia_invalida(self):
        with pytest.raises(ValueError):
            InerciaMotoBomba.thorley_faithfull(0.0, 1750.0)

    def test_rotacao_invalida(self):
        with pytest.raises(ValueError):
            InerciaMotoBomba.thorley_faithfull(21.0, -100.0)


class TestEnergiaCinetica:
    def test_formula_basica(self):
        I = 0.5   # kg·m²
        rpm = 1450.0
        omega = rpm * 2 * math.pi / 60
        esperado = 0.5 * I * omega**2
        assert math.isclose(InerciaMotoBomba.energia_cinetica(I, rpm), esperado, rel_tol=1e-9)

    def test_energia_proporcional_a_inercia(self):
        ec1 = InerciaMotoBomba.energia_cinetica(0.5, 1450.0)
        ec2 = InerciaMotoBomba.energia_cinetica(1.0, 1450.0)
        assert math.isclose(ec2 / ec1, 2.0, rel_tol=1e-9)

    def test_energia_proporcional_ao_quadrado_da_rotacao(self):
        ec1 = InerciaMotoBomba.energia_cinetica(1.0, 1000.0)
        ec2 = InerciaMotoBomba.energia_cinetica(1.0, 2000.0)
        assert math.isclose(ec2 / ec1, 4.0, rel_tol=1e-9)


class TestConversaoGD2:
    def test_gd2_para_inercia(self):
        gd2 = 0.4
        assert math.isclose(InerciaMotoBomba.gd2_para_inercia(gd2), 0.1, rel_tol=1e-9)

    def test_inercia_para_gd2(self):
        I = 0.1
        assert math.isclose(InerciaMotoBomba.inercia_para_gd2(I), 0.4, rel_tol=1e-9)

    def test_round_trip(self):
        I = 0.0765
        assert math.isclose(
            InerciaMotoBomba.gd2_para_inercia(InerciaMotoBomba.inercia_para_gd2(I)),
            I,
            rel_tol=1e-9,
        )

    def test_gd2_invalido(self):
        with pytest.raises(ValueError):
            InerciaMotoBomba.gd2_para_inercia(-0.1)

    def test_inercia_invalida(self):
        with pytest.raises(ValueError):
            InerciaMotoBomba.inercia_para_gd2(-0.1)


class TestComparacaoCatalogoSulzer:
    """
    Validação dos métodos empíricos contra o catálogo da Sulzer XFP150G CB1 60HZ.

    Dados do catálogo (Figura 5.3 — Castro, M.A.H., UFC):
      - Potência consumida : 19,7 kW
      - Power input        : 21,0 kW
      - Rotação            : ~3500 rpm  (motor 2 polos / 60 Hz)
      - I catálogo         : 0,0944 kg·m²  (valor real do fabricante)

    Os testes verificam que Thorley-Faithfull subestima I entre 15% e 25%
    para esta bomba submersível — erro admissível para estimativa preliminar,
    mas confirma que o valor de catálogo deve ser sempre preferido.
    """

    I_CATALOGO = 0.0944   # kg·m²  — Sulzer XFP150G CB1 60HZ
    ROT_RPM = 3500.0
    P_CONSUMIDA_KW = 19.7
    P_INPUT_KW = 21.0

    def test_thorley_com_potencia_consumida_subestima_ate_25_porcento(self):
        res = InerciaMotoBomba.thorley_faithfull(self.P_CONSUMIDA_KW, self.ROT_RPM)
        erro_relativo = (res.inercia_total_kg_m2 - self.I_CATALOGO) / self.I_CATALOGO
        # Deve subestimar (negativo) e não errar mais que 25 %
        assert erro_relativo < 0, "Thorley-Faithfull deve subestimar I para esta bomba"
        assert erro_relativo > -0.25, f"Erro de {erro_relativo:.1%} excede 25 % de tolerância"

    def test_thorley_com_power_input_subestima_ate_20_porcento(self):
        res = InerciaMotoBomba.thorley_faithfull(self.P_INPUT_KW, self.ROT_RPM)
        erro_relativo = (res.inercia_total_kg_m2 - self.I_CATALOGO) / self.I_CATALOGO
        assert erro_relativo < 0, "Thorley-Faithfull deve subestimar I para esta bomba"
        assert erro_relativo > -0.20, f"Erro de {erro_relativo:.1%} excede 20 % de tolerância"

    def test_power_input_mais_proximo_que_potencia_consumida(self):
        res_cons = InerciaMotoBomba.thorley_faithfull(self.P_CONSUMIDA_KW, self.ROT_RPM)
        res_input = InerciaMotoBomba.thorley_faithfull(self.P_INPUT_KW, self.ROT_RPM)
        erro_cons = abs(res_cons.inercia_total_kg_m2 - self.I_CATALOGO)
        erro_input = abs(res_input.inercia_total_kg_m2 - self.I_CATALOGO)
        assert erro_input < erro_cons, "Power input deve dar resultado mais próximo do catálogo"

    def test_energia_cinetica_real_com_catalogo(self):
        ec = InerciaMotoBomba.energia_cinetica(self.I_CATALOGO, self.ROT_RPM)
        # Ec = 0,5 * 0,0944 * (3500 * 2π/60)² ≈ 6341 J
        assert math.isclose(ec, 6341.0, rel_tol=0.01)

    def test_gd2_equivalente_do_catalogo(self):
        gd2 = InerciaMotoBomba.inercia_para_gd2(self.I_CATALOGO)
        assert math.isclose(gd2, 0.3776, rel_tol=1e-4)
