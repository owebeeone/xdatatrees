"""doc_tests.py

Unit‑tests for all runnable examples in the *DOCUMENTATION.md* file.

Run them with:
    pytest doc_tests.py

These tests require the third‑party **lxml** package because XDataTrees' recommended XML backend is *lxml.etree* for full namespace support.
"""

# ---------------------------------------------------------------------------
# Standard + third‑party deps
# ---------------------------------------------------------------------------
from typing import List, Optional, Tuple

import numpy as np   # Used by the matrix / mesh examples
import pytest        # Test runner
from lxml import etree as ET  # XDataTrees works best with lxml's ElementTree API

# ---------------------------------------------------------------------------
# Library‑under‑test imports
#   * xdatatrees is a standalone package (not inside datatrees)
#   * datatrees supplies low‑level utilities used by converters/collectors
# ---------------------------------------------------------------------------
from xdatatrees import (
    xdatatree,
    xfield,
    Attribute,
    TextContent,
    TextElement,
    Element,
    Metadata,
    XmlSerializationSpec,
    XmlNamespaces,
    XmlParserOptions,
    ValueCollector,
    TooManyValuesError,
    CamelSnakeConverter,
    SnakeCamelConverter,
)

from datatrees import datatree, dtfield

# ---------------------------------------------------------------------------
# 1. Simple Person example (Attribute + TextElement)
# ---------------------------------------------------------------------------

@xdatatree
class Person:
    name: str = xfield(ftype=Attribute)
    age: int = xfield(ftype=Attribute)
    address: str = xfield(ftype=TextElement)

PERSON_SPEC = XmlSerializationSpec(Person, "person")

PERSON_XML = (
    "<person name=\"John\" age=\"30\">"
    "<address>123 Main St</address>"
    "</person>"
)


def test_person_roundtrip():
    xml_in = ET.fromstring(PERSON_XML)
    person, status = PERSON_SPEC.deserialize(xml_in)
    assert status.contains_unknown_elements is False
    assert status.contains_unknown_attributes is False
    assert person.name == "John"
    assert person.age == 30
    assert person.address == "123 Main St"

    xml_out = PERSON_SPEC.serialize(person)
    assert ET.tostring(xml_out, encoding="unicode") == PERSON_XML
    
def test_address_text_content_roundtrip():

    @xdatatree
    class Address:
        label: str = xfield(default='work', ftype=Attribute, doc='address label')
        address: str = xfield(ftype=TextContent)

    @xdatatree
    class Person:
        name: str = xfield(ftype=Attribute)  
        age: int = xfield(ftype=Attribute)
        address: Address = xfield(ftype=Element)
        
        
    N_PERSON_SPEC = XmlSerializationSpec(
        Person, "person", options=XmlParserOptions(
            print_unused_elements=True, 
            print_unused_attributes=True))

    N_PERSON_XML = (
        "<person name=\"John\" age=\"30\">"
        "<address>123 Main St</address>"
        "</person>")
    
    xml_in = ET.fromstring(N_PERSON_XML)
    person, status = N_PERSON_SPEC.deserialize(xml_in)
    assert status.contains_unknown_elements is False
    assert status.contains_unknown_attributes is False
    assert person.name == "John"
    assert person.age == 30
    assert person.address.address == "123 Main St"
    assert person.address.label == "work"

    xml_out = N_PERSON_SPEC.serialize(person)
    assert xml_out.tag == "person"
    assert xml_out.attrib["name"] == "John"
    assert xml_out.attrib["age"] == "30"
    assert xml_out.find("address").text == "123 Main St"
    assert xml_out.find("address").attrib["label"] == "work"


# ---------------------------------------------------------------------------
# 2. People example with list handling
# ---------------------------------------------------------------------------

@xdatatree
class People:
    XDATATREE_CONFIG = xfield(ftype=Element)  # default sub‑elements
    people: List[Person] = xfield()
    count: int = xfield(ftype=Attribute)

PEOPLE_SPEC = XmlSerializationSpec(People, "people")


@pytest.fixture()
def sample_people() -> People:
    return People(
        count=2,
        people=[
            Person(name="John", age=30, address="123 Main St"),
            Person(name="Jane", age=25, address="456 Oak Ave"),
        ],
    )


def test_people_roundtrip(sample_people: People):
    xml_elem = PEOPLE_SPEC.serialize(sample_people)
    xml_str = ET.tostring(xml_elem, encoding="unicode")

    parsed, status = PEOPLE_SPEC.deserialize(xml_elem)
    assert parsed.count == 2
    assert len(parsed.people) == 2
    assert parsed.people[1].name == "Jane"
    # confirm round‑trip integrity
    assert ET.tostring(PEOPLE_SPEC.serialize(parsed), encoding="unicode") == xml_str


# ---------------------------------------------------------------------------
# 3. Custom Converter (MatrixConverter) + Metadata field example
# ---------------------------------------------------------------------------

@datatree
class MatrixConverter:
    """Converter that stores a 4×4 matrix as space‑separated text."""

    matrix: np.ndarray = dtfield()

    def __init__(self, data):
        if isinstance(data, str):
            values = [float(x) for x in data.split()]
            if len(values) != 16:
                raise ValueError("Matrix string must have 16 numbers")
            self.matrix = np.array(values).reshape(4, 4)
        else:
            self.matrix = np.asarray(data, dtype=float).reshape(4, 4)

    def __str__(self):
        return " ".join(str(x) for x in self.matrix.flatten())


@xdatatree
class Transform:
    XDATATREE_CONFIG = xfield(ftype=Metadata)
    id: str = xfield(ftype=Attribute)
    matrix: MatrixConverter = xfield()

TRANSFORM_SPEC = XmlSerializationSpec(Transform, "transform")


def test_transform_roundtrip():
    mat = np.eye(4)
    t1 = Transform(id="T1", matrix=MatrixConverter(mat))
    elem = TRANSFORM_SPEC.serialize(t1)
    text = ET.tostring(elem, encoding="unicode")

    restored, _ = TRANSFORM_SPEC.deserialize(elem)
    assert np.allclose(restored.matrix.matrix, mat)
    assert restored.id == "T1"
    assert ET.tostring(TRANSFORM_SPEC.serialize(restored), encoding="unicode") == text


# ---------------------------------------------------------------------------
# 4. Namespace handling example (Component)
# ---------------------------------------------------------------------------

NAMESPACES = XmlNamespaces(
    xmlns="http://schemas.example.com/model/2023",
    geom="http://schemas.example.com/geometry/2023",
    mat="http://schemas.example.com/materials/2023",
)


@xdatatree
class Component:
    XDATATREE_CONFIG = xfield(xmlns=NAMESPACES.xmlns, ftype=Attribute)
    id: str = xfield()
    geometry_ref: str = xfield(xmlns=NAMESPACES.geom)
    material_id: str = xfield(xmlns=NAMESPACES.mat)

COMPONENT_SPEC = XmlSerializationSpec(Component, "component", xml_namespaces=NAMESPACES)


def test_namespace_component_roundtrip():
    comp = Component(id="C1", geometry_ref="G1", material_id="M1")
    elem = COMPONENT_SPEC.serialize(comp)

    # Ensure xmlns declarations exist (lxml keeps them on serialization)
    assert elem.tag.endswith("component")
    geom_key = f"{{{NAMESPACES.geom}}}geometry_ref"
    assert geom_key in elem.attrib and elem.attrib[geom_key] == "G1"

    parsed, _ = COMPONENT_SPEC.deserialize(elem)
    assert parsed.geometry_ref == "G1"
    assert parsed.material_id == "M1"


# ---------------------------------------------------------------------------
# 5. Comprehensive Mesh/Model example (uses many features)
# ---------------------------------------------------------------------------

DEFAULT_ATTR = xfield(xmlns=NAMESPACES.xmlns, ftype=Attribute)
DEFAULT_ELEM = xfield(xmlns=NAMESPACES.xmlns, ftype=Element)


@xdatatree
class Vertex:
    XDATATREE_CONFIG = DEFAULT_ATTR
    x: float = xfield()
    y: float = xfield()
    z: float = xfield()


@xdatatree
class Triangle:
    XDATATREE_CONFIG = DEFAULT_ATTR
    v1: int = xfield()
    v2: int = xfield()
    v3: int = xfield()


@xdatatree
class Material:
    XDATATREE_CONFIG = xfield(xmlns=NAMESPACES.mat, ftype=Attribute)
    id: str = xfield()
    name: str = xfield()
    color: str = xfield()


@xdatatree
class Mesh:
    XDATATREE_CONFIG = DEFAULT_ELEM
    material_id: str = xfield(ftype=Attribute)
    vertices: List[Vertex] = xfield()
    triangles: List[Triangle] = xfield()


@xdatatree
class Model:
    XDATATREE_CONFIG = DEFAULT_ELEM
    name: str = xfield(ftype=Attribute)
    materials: List[Material] = xfield()
    meshes: List[Mesh] = xfield()

MODEL_SPEC = XmlSerializationSpec(
    Model,
    "model",
    xml_namespaces=NAMESPACES,
    options=XmlParserOptions(assert_unused_elements=True),
)


def test_mesh_model_roundtrip():
    cube = Model(
        name="Cube",
        materials=[Material(id="mat1", name="Red", color="#FF0000")],
        meshes=[
            Mesh(
                material_id="mat1",
                vertices=[
                    Vertex(0.0, 0.0, 0.0),
                    Vertex(1.0, 0.0, 0.0),
                    Vertex(1.0, 1.0, 0.0),
                    Vertex(0.0, 1.0, 0.0),
                ],
                triangles=[Triangle(0, 1, 2), Triangle(0, 2, 3)],
            )
        ],
    )
    elem = MODEL_SPEC.serialize(cube)
    xml_str = ET.tostring(elem, encoding="unicode")

    restored, status = MODEL_SPEC.deserialize(elem)
    assert status.contains_unknown_elements is False
    assert restored.name == "Cube"
    assert len(restored.meshes[0].vertices) == 4
    assert ET.tostring(MODEL_SPEC.serialize(restored), encoding="unicode") == xml_str


# ---------------------------------------------------------------------------
# 6. Name transformation example
# ---------------------------------------------------------------------------

@xdatatree
class APIResponse:
    XDATATREE_CONFIG = xfield(
        aname_transform=SnakeCamelConverter,  # snake_case -> CamelCase for attributes
        ename_transform=CamelSnakeConverter,  # CamelCase -> snake_case for elements
        ftype=Attribute,
    )
    user_id: str = xfield()  # will become 'UserId' attribute in XML
    creation_date: str = xfield(ftype=TextElement)  # will remain 'creation_date' element
    ModificationDate: str = xfield(ftype=TextElement)  # will become 'modification_date' element


API_SPEC = XmlSerializationSpec(APIResponse, "api_response")


def test_name_transformation_roundtrip():
    response = APIResponse(user_id="test_user", creation_date="2024-01-01", ModificationDate="2024-01-02")
    elem = API_SPEC.serialize(response)
    xml_str = ET.tostring(elem, encoding="unicode")

    assert 'UserId="test_user"' in xml_str
    assert "<creation_date>2024-01-01</creation_date>" in xml_str
    assert "<modification_date>2024-01-02</modification_date>" in xml_str

    xml_input = '<api_response UserId="test_user">' \
                '<creation_date>2024-01-01</creation_date>' \
                '<modification_date>2024-01-02</modification_date>'\
                '</api_response>'
                
    assert xml_input == xml_str
    
    # Deserialization test
    tree = ET.fromstring(xml_input)
    parsed_response, status = API_SPEC.deserialize(tree)
    assert parsed_response.user_id == "test_user"
    assert parsed_response.creation_date == "2024-01-01"
    assert parsed_response.ModificationDate == "2024-01-02"

# ---------------------------------------------------------------------------
# 7. Custom Value Collector example (TriangleCollector)
# ---------------------------------------------------------------------------

@xdatatree
class ColoredTriangle:
    v1: int = xfield(ftype=Attribute)
    v2: int = xfield(ftype=Attribute)
    v3: int = xfield(ftype=Attribute)
    color: str = xfield(ftype=Attribute)


@datatree
class TriangleCollector(ValueCollector):
    """Collects triangles into numpy arrays."""

    CONTAINED_TYPE = ColoredTriangle
    triangles: List[ColoredTriangle] = dtfield(default_factory=list)

    def append(self, item: ColoredTriangle):
        self.triangles.append(item)

    def get(self):
        """Returns a tuple of numpy arrays for vertices and a list of colors."""
        if not self.triangles:
            return np.array([]).reshape(0, 3), []
        vertices = np.array([[t.v1, t.v2, t.v3] for t in self.triangles])
        colors = [t.color for t in self.triangles]
        return vertices, colors

    @classmethod
    def to_contained_type(cls, data: tuple):
        """Converts collected data back to a list of Triangles."""
        vertices, colors = data
        return [
            ColoredTriangle(v1=v[0], v2=v[1], v3=v[2], color=c)
            for v, c in zip(vertices, colors)
        ]


@xdatatree
class TriangleCollectorMesh:
    triangles: List[ColoredTriangle] = xfield(ftype=Element)


MESH_SPEC = XmlSerializationSpec(TriangleCollectorMesh, "mesh")


def test_triangle_collector_roundtrip():
    triangles_data = [
        ColoredTriangle(v1=0, v2=1, v3=2, color="red"),
        ColoredTriangle(v1=2, v2=3, v3=0, color="blue"),
    ]
    mesh = TriangleCollectorMesh(triangles=triangles_data)

    elem = MESH_SPEC.serialize(mesh)
    xml_str = ET.tostring(elem, encoding="unicode")
    
    assert '<triangles v1="0" v2="1" v3="2" color="red"/>' in xml_str
    assert '<triangles v1="2" v2="3" v3="0" color="blue"/>' in xml_str

    restored_mesh, status = MESH_SPEC.deserialize(elem)
    
    assert len(restored_mesh.triangles) == 2
    assert restored_mesh.triangles[0].v1 == 0
    assert restored_mesh.triangles[1].color == "blue"

# ---------------------------------------------------------------------------
# 8. Error Handling example (TooManyValuesError)
# ---------------------------------------------------------------------------

@xdatatree
class SingleValue:
    name: str = xfield(ftype=TextElement)


SINGLE_VALUE_SPEC = XmlSerializationSpec(SingleValue, "single_value")


def test_too_many_values_error():
    xml_input = "<single_value><name>A</name><name>B</name></single_value>"
    xml_tree = ET.fromstring(xml_input)

    with pytest.raises(TooManyValuesError):
        SINGLE_VALUE_SPEC.deserialize(xml_tree)


if __name__ == "__main__":
    test_address_text_content_roundtrip()
    import pytest
    pytest.main([__file__])

