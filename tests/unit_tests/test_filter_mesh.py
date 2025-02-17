import math

import numpy as np
from uncertainties import unumpy

import openmc


def test_spherical_mesh_estimators(run_in_tmpdir):
    """Test that collision/tracklength estimators agree for SphericalMesh"""

    mat = openmc.Material()
    mat.add_nuclide('U235', 1.0)
    mat.set_density('g/cm3', 10.0)

    sphere = openmc.Sphere(r=10.0, boundary_type='vacuum')
    cell = openmc.Cell(fill=mat, region=-sphere)
    model = openmc.Model()
    model.geometry = openmc.Geometry([cell])
    model.settings.particles = 1_000
    model.settings.inactive = 10
    model.settings.batches = 20

    sph_mesh = openmc.SphericalMesh()
    sph_mesh.r_grid = np.linspace(0.0, 5.0**3, 20)**(1/3)
    tally1 = openmc.Tally()
    tally1.filters = [openmc.MeshFilter(sph_mesh)]
    tally1.scores = ['flux']
    tally1.estimator = 'collision'

    sph_mesh = openmc.SphericalMesh()
    sph_mesh.r_grid = np.linspace(0.0, 5.0**3, 20)**(1/3)
    tally2 = openmc.Tally()
    tally2.filters = [openmc.MeshFilter(sph_mesh)]
    tally2.scores = ['flux']
    tally2.estimator = 'tracklength'

    model.tallies = openmc.Tallies([tally1, tally2])

    # Run OpenMC
    sp_filename = model.run()

    # Get radial flux distribution
    with openmc.StatePoint(sp_filename) as sp:
        flux_collision = sp.tallies[tally1.id].mean.ravel()
        flux_collision_unc = sp.tallies[tally1.id].std_dev.ravel()
        flux_tracklength = sp.tallies[tally2.id].mean.ravel()
        flux_tracklength_unc = sp.tallies[tally2.id].std_dev.ravel()

    # Construct arrays with uncertainties
    collision = unumpy.uarray(flux_collision, flux_collision_unc)
    tracklength = unumpy.uarray(flux_tracklength, flux_tracklength_unc)
    delta = collision - tracklength

    # Check that difference is within uncertainty
    diff = unumpy.nominal_values(delta)
    std_dev = unumpy.std_devs(delta)
    assert np.all(diff < 3*std_dev)


def test_cylindrical_mesh_estimators(run_in_tmpdir):
    """Test that collision/tracklength estimators agree for CylindricalMesh"""

    mat = openmc.Material()
    mat.add_nuclide('U235', 1.0)
    mat.set_density('g/cm3', 10.0)

    cyl = openmc.model.RightCircularCylinder((0., 0., -5.), 10., 10.0,
                                             boundary_type='vacuum')
    cell = openmc.Cell(fill=mat, region=-cyl)
    model = openmc.Model()
    model.geometry = openmc.Geometry([cell])
    model.settings.particles = 1_000
    model.settings.inactive = 10
    model.settings.batches = 20

    cyl_mesh = openmc.CylindricalMesh()
    cyl_mesh.r_grid = np.linspace(0.0, 5.0**3, 20)**(1/3)
    cyl_mesh.z_grid = [-5., 5.]
    tally1 = openmc.Tally()
    tally1.filters = [openmc.MeshFilter(cyl_mesh)]
    tally1.scores = ['flux']
    tally1.estimator = 'collision'

    cyl_mesh = openmc.CylindricalMesh()
    cyl_mesh.r_grid = np.linspace(0.0, 5.0**3, 20)**(1/3)
    cyl_mesh.z_grid = [-5., 5.]
    tally2 = openmc.Tally()
    tally2.filters = [openmc.MeshFilter(cyl_mesh)]
    tally2.scores = ['flux']
    tally2.estimator = 'tracklength'

    model.tallies = openmc.Tallies([tally1, tally2])

    # Run OpenMC
    sp_filename = model.run()

    # Get radial flux distribution
    with openmc.StatePoint(sp_filename) as sp:
        flux_collision = sp.tallies[tally1.id].mean.ravel()
        flux_collision_unc = sp.tallies[tally1.id].std_dev.ravel()
        flux_tracklength = sp.tallies[tally2.id].mean.ravel()
        flux_tracklength_unc = sp.tallies[tally2.id].std_dev.ravel()

    # Construct arrays with uncertainties
    collision = unumpy.uarray(flux_collision, flux_collision_unc)
    tracklength = unumpy.uarray(flux_tracklength, flux_tracklength_unc)
    delta = collision - tracklength

    # Check that difference is within uncertainty
    diff = unumpy.nominal_values(delta)
    std_dev = unumpy.std_devs(delta)
    assert np.all(diff < 3*std_dev)

def test_get_reshaped_data(run_in_tmpdir):
    """Test that expanding MeshFilter dimensions works as expected"""

    mat = openmc.Material()
    mat.add_nuclide('U235', 1.0)
    mat.set_density('g/cm3', 10.0)

    sphere = openmc.Sphere(r=10.0, boundary_type='vacuum')
    cell = openmc.Cell(fill=mat, region=-sphere)
    model = openmc.Model()
    model.geometry = openmc.Geometry([cell])
    model.settings.particles = 1_000
    model.settings.inactive = 10
    model.settings.batches = 20

    sph_mesh = openmc.SphericalMesh()
    sph_mesh.r_grid = np.linspace(0.0, 5.0**3, 20)**(1/3)
    sph_mesh.theta_grid = np.linspace(0, math.pi, 4)
    sph_mesh.phi_grid = np.linspace(0, 2*math.pi, 3)
    tally1 = openmc.Tally()
    efilter = openmc.EnergyFilter([0, 1e5, 1e8])
    meshfilter = openmc.MeshFilter(sph_mesh)
    assert meshfilter.shape == (19, 3, 2)
    tally1.filters = [efilter, meshfilter]
    tally1.scores = ['flux']

    model.tallies = openmc.Tallies([tally1])

    # Run OpenMC
    sp_filename = model.run()

    # Get flux tally as reshaped data
    with openmc.StatePoint(sp_filename) as sp:
        t1 = sp.tallies[tally1.id]
        data1 = t1.get_reshaped_data()
        data2 = t1.get_reshaped_data(expand_dims=True)

    assert data1.shape == (2, 19*3*2, 1, 1)
    assert data2.shape == (2, 19, 3, 2, 1, 1)
