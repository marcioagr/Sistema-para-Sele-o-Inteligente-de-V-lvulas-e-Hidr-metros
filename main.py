#!/usr/bin/env python3
"""
Calculadora de Momento de Inércia Polar — Conjunto Moto-bomba

Baseado em:
  Castro, M.A.H. - Momento de Inércia - Aula UFC (seção 5.1)

Métodos disponíveis:
  1. Geométrico — Cilindro Maciço
  2. Geométrico — Cilindro Oco (anel)
  3. Empírico   — Koelle e Betâmio (1992)
  4. Empírico   — Thorley e Faithfull (1992)
  5. Conversão  — GD² ↔ Inércia
  6. Energia cinética acumulada
"""

import sys
from src.calculos.inercia_moto_bomba import InerciaMotoBomba


SEPARADOR = "─" * 60


def cabecalho():
    print()
    print("=" * 60)
    print("  CÁLCULO DO MOMENTO DE INÉRCIA POLAR — MOTO-BOMBA")
    print("  Ref.: Castro, M.A.H. — UFC (seção 5.1.1)")
    print("=" * 60)


def menu_principal() -> str:
    print()
    print(SEPARADOR)
    print("  Escolha o método de cálculo:")
    print(SEPARADOR)
    print("  [1] Geométrico — Cilindro Maciço")
    print("  [2] Geométrico — Cilindro Oco (anel)")
    print("  [3] Empírico   — Koelle e Betâmio (1992)")
    print("  [4] Empírico   — Thorley e Faithfull (1992)")
    print("  [5] Conversão  — GD² ↔ Inércia Polar")
    print("  [6] Energia Cinética Acumulada")
    print("  [0] Sair")
    print(SEPARADOR)
    return input("  Opção: ").strip()


def ler_float(prompt: str, minimo: float = 0.0, exclusivo: bool = True) -> float:
    while True:
        try:
            valor = float(input(f"  {prompt}: ").replace(",", "."))
            if exclusivo and valor <= minimo:
                print(f"  Valor deve ser > {minimo}. Tente novamente.")
            elif not exclusivo and valor < minimo:
                print(f"  Valor deve ser >= {minimo}. Tente novamente.")
            else:
                return valor
        except ValueError:
            print("  Entrada inválida. Use número (ex: 1,5 ou 1.5).")


def exibir_resultado(resultado, rotacao_rpm: float = None):
    print()
    print(SEPARADOR)
    print(resultado)
    if rotacao_rpm is not None and rotacao_rpm > 0:
        ec = InerciaMotoBomba.energia_cinetica(resultado.inercia_total_kg_m2, rotacao_rpm)
        print(f"  Energia Cinética      : {ec:.2f} J  (a {rotacao_rpm:.0f} rpm)")
    gd2 = InerciaMotoBomba.inercia_para_gd2(resultado.inercia_total_kg_m2)
    print(f"  GD² equivalente       : {gd2:.6f} kg·m²")
    print(SEPARADOR)


def calcular_cilindro_macico():
    print()
    print("  >> Cilindro Maciço (Eq. 5.5 / 5.4)")
    print("     I = m·r²/2  |  D² = d²/2  |  GD² = m·D²")
    print()
    massa = ler_float("Massa do rotor (kg)")
    diametro = ler_float("Diâmetro do cilindro (m)")
    resultado = InerciaMotoBomba.cilindro_macico(massa, diametro)
    exibir_resultado(resultado)


def calcular_cilindro_oco():
    print()
    print("  >> Cilindro Oco — Anel (Eq. 5.6 / 5.7)")
    print("     I = m·(r1²+r2²)/2  |  D² = (d1²+d2²)/2")
    print()
    massa = ler_float("Massa do rotor (kg)")
    d_int = ler_float("Diâmetro interno (m)")
    d_ext = ler_float("Diâmetro externo (m)")
    if d_int >= d_ext:
        print("  ERRO: diâmetro interno deve ser menor que o externo.")
        return
    resultado = InerciaMotoBomba.cilindro_oco(massa, d_int, d_ext)
    exibir_resultado(resultado)


def calcular_koelle_betamio():
    print()
    print("  >> Koelle e Betâmio (1992) — Eq. 5.8")
    print("     I = 288 · (P / N0)^1,435")
    print("     P em HP, N0 em rpm")
    print("     ATENÇÃO: não aplicar em bombas multiestágio.")
    print()
    pot_hp = ler_float("Potência da bomba (HP)")
    rot = ler_float("Rotação em estado permanente (rpm)")
    resultado = InerciaMotoBomba.koelle_betamio(pot_hp, rot)
    exibir_resultado(resultado, rotacao_rpm=rot)


def calcular_thorley_faithfull():
    print()
    print("  >> Thorley e Faithfull (1992) — Eq. 5.9 e 5.10")
    print("     I1 = 0,038 · [P/(N0/1000)³]^0,96  (rotor + fluido)")
    print("     I2 = 0,0043 · [P/(N0/1000)]^1,48  (motor)")
    print("     I  = I1 + I2      P em kW, N0 em rpm")
    print("     ATENÇÃO: não aplicar em bombas multiestágio.")
    print()
    pot_kw = ler_float("Potência do conjunto (kW)")
    rot = ler_float("Rotação em estado permanente (rpm)")
    resultado = InerciaMotoBomba.thorley_faithfull(pot_kw, rot)
    exibir_resultado(resultado, rotacao_rpm=rot)


def calcular_conversao():
    print()
    print("  >> Conversão GD² ↔ Inércia Polar (Eq. 5.4)")
    print("     I = GD² / 4    |    GD² = 4 · I")
    print()
    print("  [1] GD² → Inércia (I = GD²/4)")
    print("  [2] Inércia → GD² (GD² = 4·I)")
    op = input("  Opção: ").strip()
    if op == "1":
        gd2 = ler_float("GD² (kg·m²)", minimo=0.0, exclusivo=False)
        I = InerciaMotoBomba.gd2_para_inercia(gd2)
        print()
        print(SEPARADOR)
        print(f"  GD²      : {gd2:.6f} kg·m²")
        print(f"  Inércia I: {I:.6f} kg·m²")
        print(SEPARADOR)
    elif op == "2":
        I = ler_float("Inércia I (kg·m²)", minimo=0.0, exclusivo=False)
        gd2 = InerciaMotoBomba.inercia_para_gd2(I)
        print()
        print(SEPARADOR)
        print(f"  Inércia I: {I:.6f} kg·m²")
        print(f"  GD²      : {gd2:.6f} kg·m²")
        print(SEPARADOR)
    else:
        print("  Opção inválida.")


def calcular_energia_cinetica():
    print()
    print("  >> Energia Cinética (Eq. 5.2)")
    print("     Ec = I · ω² / 2      ω = N0 · 2π / 60  (rad/s)")
    print()
    I = ler_float("Inércia Polar I (kg·m²)")
    rot = ler_float("Rotação (rpm)")
    ec = InerciaMotoBomba.energia_cinetica(I, rot)
    import math
    omega = rot * 2 * math.pi / 60
    print()
    print(SEPARADOR)
    print(f"  Inércia I         : {I:.6f} kg·m²")
    print(f"  Rotação           : {rot:.0f} rpm  ({omega:.2f} rad/s)")
    print(f"  Energia Cinética  : {ec:.2f} J")
    print(SEPARADOR)


ACOES = {
    "1": calcular_cilindro_macico,
    "2": calcular_cilindro_oco,
    "3": calcular_koelle_betamio,
    "4": calcular_thorley_faithfull,
    "5": calcular_conversao,
    "6": calcular_energia_cinetica,
}


def main():
    cabecalho()
    while True:
        opcao = menu_principal()
        if opcao == "0":
            print("\n  Encerrando. Até logo!\n")
            sys.exit(0)
        acao = ACOES.get(opcao)
        if acao is None:
            print("  Opção inválida. Tente novamente.")
            continue
        try:
            acao()
        except ValueError as e:
            print(f"\n  ERRO: {e}")
        except KeyboardInterrupt:
            print("\n  Operação cancelada.")


if __name__ == "__main__":
    main()
