from math import cos, pi

def OceanScienceCalculation():
    '''
    The following is an estimate of DOC in the ocean.
    DOC Dissolved organic carbon in the ocean is ~1000 GTons. Inorganic carbon: 38,000 GTons.
    Near the ocean surface: 100 - 500 micromoles of carbon per kg seawater. The concentration 
    decreases with depth so for the entire water column we can use an attenuation factor 
    of (1/7.5). 
    '''
    radius_earth_meters      = 6378000
    pi                       = 3.141592654
    ocean_percent            = 71
    ocean_mean_depth_meters  = 3700
    water_kg_per_m3          = 1000
    ocean_volume_m3          = 4. * pi * radius_earth_meters**2 * (ocean_percent / 100.) * ocean_mean_depth_meters
    GTons_per_kg             = 1e-12
    ocean_mass_kg            = ocean_volume_m3 * water_kg_per_m3
    ocean_mass_GTons         = ocean_mass_kg * GTons_per_kg

    carbon_surface_um_per_kg = 300
    micromoles_per_mole      = 1e6
    moles_per_micromole      = 1/micromoles_per_mole
    depth_attenuation        = 1/7.5
    carbon_moles_per_kg      = carbon_surface_um_per_kg * moles_per_micromole * depth_attenuation
    carbon_gm_per_mole       = 12
    gm_per_kg                = 1000
    kg_per_gm                = 1 / gm_per_kg
    
    carbon_kg_per_kg         = carbon_moles_per_kg * carbon_gm_per_mole * kg_per_gm
    carbon_in_the_ocean_kg   = ocean_mass_kg * carbon_kg_per_kg
    carbon_in_ocean_GTons    = GTons_per_kg * carbon_in_the_ocean_kg
    
    print("Mass of earth's oceans:", '{:0.2e}'.format(ocean_mass_GTons), 'GTons')
    print("Organic carbon (kg) dissolved per kg of seawater:", round(carbon_kg_per_kg, 12))
    print("Dissolved organic carbon mass, earth's oceans:", round(carbon_in_ocean_GTons, 1), 'GTons')
    print()


# The Oregon coast has a longitude of approximately 124 degrees west
# The three shallow profiler sites are located some distance further west.
def OffshoreDistanceFromNewportOregon(lon):
    '''
    Regional Cabled Array (RCA)-specific calculation. Returns the distance (km) 
    of some site by longitude relative to Newport on the Oregon coast. The
    hardcoded reference location is 44.6 deg north, -124 deg west.
    '''
    ref_lat, ref_lon = 44.6*pi/180, -124*pi/180
    re               = 6378.     # earth radius, kilometers
    return abs(lon*pi/180 - ref_lon)*cos(ref_lat)*re