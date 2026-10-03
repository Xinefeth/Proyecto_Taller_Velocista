#include <unity.h>

#include "linea.h"

using linea::calcularError;

void setUp() {}
void tearDown() {}

static void lineaEnSensores(uint16_t* v, int a, int b) {
  for (int i = 0; i < linea::CANALES; i++) v[i] = (i == a || i == b) ? 1000 : 0;
}

void test_linea_centrada_da_cero() {
  uint16_t v[16];
  lineaEnSensores(v, 7, 8);
  float e = 99;
  TEST_ASSERT_TRUE(calcularError(v, false, 300, e));
  TEST_ASSERT_FLOAT_WITHIN(0.001f, 0.0f, e);
}

void test_extremos_dan_menos_uno_y_uno() {
  uint16_t v[16];
  float e = 0;
  lineaEnSensores(v, 0, 0);
  TEST_ASSERT_TRUE(calcularError(v, false, 300, e));
  TEST_ASSERT_FLOAT_WITHIN(0.001f, -1.0f, e);
  lineaEnSensores(v, 15, 15);
  TEST_ASSERT_TRUE(calcularError(v, false, 300, e));
  TEST_ASSERT_FLOAT_WITHIN(0.001f, 1.0f, e);
}

void test_linea_perdida_no_cambia_el_error() {
  uint16_t v[16] = {0};
  float e = 0.42f;
  TEST_ASSERT_FALSE(calcularError(v, false, 300, e));
  TEST_ASSERT_FLOAT_WITHIN(0.0001f, 0.42f, e);
}

void test_linea_blanca_invierte_las_lecturas() {
  uint16_t v[16];
  for (int i = 0; i < 16; i++) v[i] = (i == 3) ? 0 : 1000;  // línea blanca sobre el sensor 3
  float e = 0;
  TEST_ASSERT_TRUE(calcularError(v, true, 300, e));
  TEST_ASSERT_FLOAT_WITHIN(0.001f, (3 - 7.5f) / 7.5f, e);
}

int main() {
  UNITY_BEGIN();
  RUN_TEST(test_linea_centrada_da_cero);
  RUN_TEST(test_extremos_dan_menos_uno_y_uno);
  RUN_TEST(test_linea_perdida_no_cambia_el_error);
  RUN_TEST(test_linea_blanca_invierte_las_lecturas);
  return UNITY_END();
}
