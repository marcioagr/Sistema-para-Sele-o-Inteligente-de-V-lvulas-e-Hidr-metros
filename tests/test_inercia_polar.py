"""Testes unitários para o módulo de cálculo da inércia polar."""

import math
import pytest
from src.calculos.inercia_polar import (
    InerciaPolar,
    MaterialValvula,
    TipoValvula,
    ResultadoInercia,
)


class TestDiscoSolido:
    def test_formula_basica(self):
        # Ip = (1/2) * m * r²
        # Cilindro: m = rho * pi * r² * h
        r = 0.05  # 50 mm → raio 50 mm
        h = 0.006
        rho = MaterialValvula.ACO_INOX_316.densidade
        m_esperada = rho * math.pi * r**2 * h
        ip_esperada = 0.5 * m_esperada * r**2

        ip, m = InerciaPolar.disco_solido(r, h, MaterialValvula.ACO_INOX_316)

        assert math.isclose(m, m_esperada, rel_tol=1e-9)
        assert math.isclose(ip, ip_esperada, rel_tol=1e-9)

    def test_proporcional_ao_raio_4(self):
        # Para mesma espessura e material, Ip ∝ r⁴
        ip1, _ = InerciaPolar.disco_solido(0.05, 0.01, MaterialValvula.ACO_CARBONO)
        ip2, _ = InerciaPolar.disco_solido(0.10, 0.01, MaterialValvula.ACO_CARBONO)
        assert math.isclose(ip2 / ip1, 2**4, rel_tol=1e-9)


class TestDiscoOco:
    def test_raio_interno_zero_igual_solido(self):
        r_ext = 0.05
        esp = 0.006
        ip_oco, m_oco = InerciaPolar.disco_oco(
            r_ext, 0.0, esp, MaterialValvula.ACO_INOX_316
        )
        ip_sol, m_sol = InerciaPolar.disco_solido(
            r_ext, esp, MaterialValvula.ACO_INOX_316
        )
        assert math.isclose(ip_oco, ip_sol, rel_tol=1e-9)
        assert math.isclose(m_oco, m_sol, rel_tol=1e-9)

    def test_formula_anel(self):
        r_ext, r_int, esp = 0.1, 0.05, 0.01
        rho = MaterialValvula.BRONZE.densidade
        volume = math.pi * (r_ext**2 - r_int**2) * esp
        m_esp = rho * volume
        ip_esp = 0.5 * m_esp * (r_ext**2 + r_int**2)

        ip, m = InerciaPolar.disco_oco(r_ext, r_int, esp, MaterialValvula.BRONZE)
        assert math.isclose(m, m_esp, rel_tol=1e-9)
        assert math.isclose(ip, ip_esp, rel_tol=1e-9)


class TestEsferaSolida:
    def test_formula_basica(self):
        r = 0.05
        rho = MaterialValvula.ACO_CARBONO.densidade
        m_esp = rho * (4 / 3) * math.pi * r**3
        ip_esp = (2 / 5) * m_esp * r**2

        ip, m = InerciaPolar.esfera_solida(r, MaterialValvula.ACO_CARBONO)
        assert math.isclose(m, m_esp, rel_tol=1e-9)
        assert math.isclose(ip, ip_esp, rel_tol=1e-9)


class TestEsferaComFuro:
    def test_furo_zero_igual_solida(self):
        r = 0.06
        ip_furo, m_furo = InerciaPolar.esfera_com_furo(
            r, 0.0, MaterialValvula.ACO_INOX_304
        )
        ip_sol, m_sol = InerciaPolar.esfera_solida(r, MaterialValvula.ACO_INOX_304)
        assert math.isclose(ip_furo, ip_sol, rel_tol=1e-9)
        assert math.isclose(m_furo, m_sol, rel_tol=1e-9)

    def test_furo_reduz_massa_e_inercia(self):
        r = 0.06
        ip_sem, m_sem = InerciaPolar.esfera_com_furo(
            r, 0.0, MaterialValvula.ACO_INOX_316
        )
        ip_com, m_com = InerciaPolar.esfera_com_furo(
            r, 0.03, MaterialValvula.ACO_INOX_316
        )
        assert m_com < m_sem
        assert ip_com < ip_sem


class TestValvulaBorboleta:
    @pytest.mark.parametrize("dn", [50, 100, 200, 300, 400])
    def test_resultado_positivo(self, dn):
        res = InerciaPolar.valvula_borboleta(dn)
        assert res.inercia_polar_kg_m2 > 0
        assert res.massa_kg > 0
        assert res.tipo_valvula == TipoValvula.BORBOLETA

    def test_inercia_cresce_com_dn(self):
        r1 = InerciaPolar.valvula_borboleta(100)
        r2 = InerciaPolar.valvula_borboleta(200)
        assert r2.inercia_polar_kg_m2 > r1.inercia_polar_kg_m2

    def test_torque_dinamico_calculado(self):
        alpha = 5.0  # rad/s²
        res = InerciaPolar.valvula_borboleta(100, aceleracao_angular_rad_s2=alpha)
        assert res.torque_dinamico_nm is not None
        assert math.isclose(
            res.torque_dinamico_nm,
            res.inercia_polar_kg_m2 * alpha,
            rel_tol=1e-9,
        )

    def test_conversao_g_cm2(self):
        res = InerciaPolar.valvula_borboleta(100)
        assert math.isclose(
            res.inercia_polar_g_cm2,
            res.inercia_polar_kg_m2 * 1e7,
            rel_tol=1e-9,
        )


class TestValvulaEsfera:
    @pytest.mark.parametrize("dn", [25, 50, 100, 150])
    def test_resultado_positivo(self, dn):
        res = InerciaPolar.valvula_esfera(dn)
        assert res.inercia_polar_kg_m2 > 0
        assert res.tipo_valvula == TipoValvula.ESFERA

    def test_full_bore_maior_que_reduced(self):
        full = InerciaPolar.valvula_esfera(100, fator_furo=1.0)
        reduced = InerciaPolar.valvula_esfera(100, fator_furo=0.6)
        # Full bore remove mais material → menor inércia
        assert full.inercia_polar_kg_m2 < reduced.inercia_polar_kg_m2


class TestValvulaPlugue:
    def test_resultado_positivo(self):
        res = InerciaPolar.valvula_plugue(50)
        assert res.inercia_polar_kg_m2 > 0
        assert res.tipo_valvula == TipoValvula.PLUGUE


class TestTempoOperacao:
    def test_maior_torque_menor_tempo(self):
        ip = 0.001  # kg·m²
        t1 = InerciaPolar.tempo_para_aceleracao(ip, 10.0)
        t2 = InerciaPolar.tempo_para_aceleracao(ip, 50.0)
        assert t1 > t2

    def test_torque_invalido(self):
        with pytest.raises(ValueError):
            InerciaPolar.tempo_para_aceleracao(0.001, 0.0)

    def test_formula_consistente(self):
        ip = 0.005
        torque = 2.0
        angulo = 90.0

        tempo = InerciaPolar.tempo_para_aceleracao(ip, torque, angulo)
        resultado = InerciaPolar.aceleracao_angular_de_tempo(ip, tempo, angulo)

        assert math.isclose(resultado["torque_dinamico_nm"], torque, rel_tol=1e-6)


class TestAceleracaoAngular:
    def test_valores_positivos(self):
        resultado = InerciaPolar.aceleracao_angular_de_tempo(0.001, 5.0)
        assert resultado["aceleracao_rad_s2"] > 0
        assert resultado["torque_dinamico_nm"] > 0

    def test_menor_tempo_maior_torque(self):
        ip = 0.002
        r_lento = InerciaPolar.aceleracao_angular_de_tempo(ip, 10.0)
        r_rapido = InerciaPolar.aceleracao_angular_de_tempo(ip, 2.0)
        assert r_rapido["torque_dinamico_nm"] > r_lento["torque_dinamico_nm"]
