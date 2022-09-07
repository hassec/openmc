
#ifndef OPENMC_INTERPOLATE_H
#define OPENMC_INTERPOLATE_H

#include <cmath>
#include <vector>

#include "openmc/search.h"

namespace openmc {

inline double interpolate_lin_lin(
  double x0, double x1, double y0, double y1, double x)
{
  return y0 + (x - x0) / (x1 - x0) * (y1 - y0);
}

inline double interpolate_lin_log(
  double x0, double x1, double y0, double y1, double x)
{
  return y0 + log(x / x0) / log(x1 / x0) * (y1 - y0);
}

inline double interpolate_log_lin(
  double x0, double x1, double y0, double y1, double x)
{
  return y0 * exp((x - x0) / (x1 - x0) * log(y1 / y0));
}

inline double interpolate_log_log(
  double x0, double x1, double y0, double y1, double x)
{
  double f = log(x / x0) / log(x1 / x0);
  return y0 * exp(f * log(y1 / y0));
}

inline double interpolate_lagrangian(
  const std::vector<double>& xs, const std::vector<double>& ys, int idx, double x, int order)
{
  std::vector<double> coeffs;

  for (int i = 0; i < order + 1; i++) {
    double numerator {1.0};
    double denominator {1.0};
    for (int j = 0; j < order; j++) {
      if (i == j)
        continue;
      numerator *= (x - xs[idx + j]);
      denominator *= (xs[idx + i] - xs[idx + j]);
    }
    coeffs.push_back(numerator / denominator);
  }

  return std::inner_product(
    coeffs.begin(), coeffs.end(), ys.begin() + idx, 0.0);
}

inline double interpolate(const std::vector<double>& xs,
  const std::vector<double>& ys, double x,
  Interpolation i = Interpolation::lin_lin)
{
  int idx = lower_bound_index(xs.begin(), xs.end(), x);

  switch (i) {
  case Interpolation::lin_lin:
    return interpolate_lin_lin(xs[idx], xs[idx + 1], ys[idx], ys[idx + 1], x);
  case Interpolation::log_log:
    return interpolate_log_log(xs[idx], xs[idx + 1], ys[idx], ys[idx + 1], x);
  case Interpolation::lin_log:
    return interpolate_lin_log(xs[idx], xs[idx + 1], ys[idx], ys[idx + 1], x);
  case Interpolation::log_lin:
    return interpolate_log_lin(xs[idx], xs[idx + 1], ys[idx], ys[idx + 1], x);
  case Interpolation::quadratic:
    // move back one point if x is in the last interval of the x-grid
    if (idx == xs.size() - 2 && idx > 0) idx--;
    return interpolate_lagrangian(xs, ys, x, idx, 2);
  case Interpolation::cubic:
    // if x is not in the first interval of the x-grid, move back one
    if (idx > 0) idx--;
    // if the index was the last interval of the x-grid, move it back one more
    if (idx == xs.size() - 3) idx--;
    return interpolate_lagrangian(xs, ys, x, idx, 3);
  default:
    fatal_error("Unsupported interpolation");
  }
}


} // namespace openmc

#endif