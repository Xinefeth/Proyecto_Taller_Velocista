#include <unity.h>

#include "vueltas.h"

void setUp() {}
void tearDown() {}

void test_primer_corte_es_la_salida() {
  CalculadorVueltas c(2000000);
  int64_t v = 0;
  TEST_ASSERT_TRUE(c.registrar(5000000, v));
  TEST_ASSERT_EQUAL_INT64(-1, v);
}

void test_tiempo_de_vuelta_en_ms() {
  CalculadorVueltas c(2000000);
  int64_t v = 0;
  c.registrar(1000000, v);
  TEST_ASSERT_TRUE(c.registrar(19342000, v));
  TEST_ASSERT_EQUAL_INT64(18342, v);
}

void test_rebote_se_descarta() {
  CalculadorVueltas c(2000000);
  int64_t v = 0;
  c.registrar(1000000, v);
  TEST_ASSERT_FALSE(c.registrar(1500000, v));
  TEST_ASSERT_EQUAL_UINT32(1, c.cortes());
}

void test_rearmar_inicia_una_salida_nueva() {
  CalculadorVueltas c(2000000);
  int64_t v = 0;
  c.registrar(1000000, v);
  c.rearmar();
  TEST_ASSERT_TRUE(c.registrar(1100000, v));
  TEST_ASSERT_EQUAL_INT64(-1, v);
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_primer_corte_es_la_salida);
  RUN_TEST(test_tiempo_de_vuelta_en_ms);
  RUN_TEST(test_rebote_se_descarta);
  RUN_TEST(test_rearmar_inicia_una_salida_nueva);
  return UNITY_END();
}
