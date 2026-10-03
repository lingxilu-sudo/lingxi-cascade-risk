"""
Physics Layer: Orbital mechanics and debris cascade simulation.
"""

from .orbital_shell import OrbitalShell
from .collision_model import CollisionModel, CollisionEvent
from .debris_growth import DebrisGrowthModel, DebrisState
from .cascade_simulator import CascadeSimulator, SimulationResult

__all__ = [
    "OrbitalShell",
    "CollisionModel",
    "CollisionEvent",
    "DebrisGrowthModel",
    "DebrisState",
    "CascadeSimulator",
    "SimulationResult",
]
