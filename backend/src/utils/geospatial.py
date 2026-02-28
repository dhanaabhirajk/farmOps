"""Geospatial utilities for S2 and H3 tiling operations."""

from typing import List, Tuple

import h3
from s2sphere import Cell, CellId, LatLng


class GeospatialUtils:
    """Utilities for geospatial operations using S2 and H3."""

    @staticmethod
    def lat_lng_to_s2_cell(lat: float, lng: float, level: int = 13) -> str:
        """
        Convert latitude/longitude to S2 cell ID at specified level.

        Args:
            lat: Latitude in degrees
            lng: Longitude in degrees
            level: S2 cell level (0-30, default 13 for ~1km²)

        Returns:
            S2 cell ID as hex string
        """
        lat_lng = LatLng.from_degrees(lat, lng)
        cell_id = CellId.from_lat_lng(lat_lng)
        # Get parent at desired level
        cell_id_at_level = cell_id.parent(level)
        return cell_id_at_level.to_token()

    @staticmethod
    def polygon_to_s2_cells(
        coordinates: List[Tuple[float, float]], level: int = 13
    ) -> List[str]:
        """
        Get S2 cells covering a polygon.

        Args:
            coordinates: List of (lat, lng) tuples defining polygon
            level: S2 cell level

        Returns:
            List of S2 cell IDs covering the polygon
        """
        # Simple implementation: get cells for all vertices
        # For production, use proper polygon coverage algorithm
        cells = set()
        for lat, lng in coordinates:
            cell_token = GeospatialUtils.lat_lng_to_s2_cell(lat, lng, level)
            cells.add(cell_token)
        return list(cells)

    @staticmethod
    def lat_lng_to_h3_cell(lat: float, lng: float, resolution: int = 9) -> str:
        """
        Convert latitude/longitude to H3 cell ID at specified resolution.

        Args:
            lat: Latitude in degrees
            lng: Longitude in degrees
            resolution: H3 resolution (0-15, default 9 for ~0.1km²)

        Returns:
            H3 cell ID as hex string
        """
        return h3.latlng_to_cell(lat, lng, resolution)

    @staticmethod
    def polygon_to_h3_cells(
        coordinates: List[Tuple[float, float]], resolution: int = 9
    ) -> List[str]:
        """
        Get H3 cells covering a polygon.

        Args:
            coordinates: List of (lat, lng) tuples defining polygon exterior ring
            resolution: H3 resolution (0-15)

        Returns:
            List of H3 cell IDs covering the polygon
        """
        # Convert to GeoJSON structure expected by h3.polygon_to_cells
        geojson_coords = [(lng, lat) for lat, lng in coordinates]
        h3_cells = h3.polygon_to_cells({"type": "Polygon", "coordinates": [geojson_coords]}, resolution)
        return list(h3_cells)

    @staticmethod
    def h3_cell_to_boundary(h3_cell: str) -> List[Tuple[float, float]]:
        """
        Get boundary vertices of an H3 cell.

        Args:
            h3_cell: H3 cell ID

        Returns:
            List of (lat, lng) tuples for cell boundary
        """
        boundary = h3.cell_to_boundary(h3_cell)
        return [(lat, lng) for lat, lng in boundary]

    @staticmethod
    def s2_cell_to_boundary(s2_token: str) -> List[Tuple[float, float]]:
        """
        Get boundary vertices of an S2 cell.

        Args:
            s2_token: S2 cell ID token

        Returns:
            List of (lat, lng) tuples for cell boundary (4 corners)
        """
        cell_id = CellId.from_token(s2_token)
        cell = Cell(cell_id)

        # Get 4 corners of the cell
        vertices = []
        for i in range(4):
            vertex = cell.get_vertex(i)
            lat_lng = LatLng.from_point(vertex)
            vertices.append((lat_lng.lat().degrees, lat_lng.lng().degrees))

        return vertices

    @staticmethod
    def get_h3_neighbors(h3_cell: str, k: int = 1) -> List[str]:
        """
        Get neighboring H3 cells within k distance.

        Args:
            h3_cell: H3 cell ID
            k: Distance in k-rings (default 1 = immediate neighbors)

        Returns:
            List of neighboring H3 cell IDs
        """
        return list(h3.grid_disk(h3_cell, k))

    @staticmethod
    def calculate_area_km2(h3_cells: List[str]) -> float:
        """
        Calculate total area covered by H3 cells in km².

        Args:
            h3_cells: List of H3 cell IDs

        Returns:
            Area in square kilometers
        """
        total_area = 0.0
        for cell in h3_cells:
            # Get area in km² for each cell
            total_area += h3.cell_area(cell, unit="km^2")
        return total_area
