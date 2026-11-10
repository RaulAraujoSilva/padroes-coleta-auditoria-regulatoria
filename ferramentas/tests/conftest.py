# -*- coding: utf-8 -*-
import copy
import sys
from pathlib import Path

import pytest

PASTA_FERRAMENTAS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PASTA_FERRAMENTAS))

from contrato import carregar_contrato  # noqa: E402
from gerador_exemplo import gerar_exemplo  # noqa: E402

CONTRATO_MINIMO = Path(__file__).with_name("contrato_minimo.yaml")


@pytest.fixture(scope="session")
def contrato():
    return carregar_contrato(CONTRATO_MINIMO)


@pytest.fixture(scope="session")
def _exemplo_base(contrato):
    return gerar_exemplo(contrato)


@pytest.fixture
def exemplo(_exemplo_base):
    """Cópia do envio de exemplo, que cada teste pode alterar à vontade."""
    return copy.deepcopy(_exemplo_base)
