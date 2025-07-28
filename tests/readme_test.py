'''
Tests for code examples in the README.md file.

'''

import unittest
import xml.etree.ElementTree as ET
import numpy as np
import re
from typing import List, Tuple, Union

# Import xdatatrees components
from xdatatrees import (
    xdatatree, xfield, Attribute, Element, Metadata, TextElement,
    XmlSerializationSpec, XmlNamespaces, XmlParserOptions,
    ValueCollector, CamelSnakeConverter, SnakeCamelConverter,
    TooManyValuesError
)
from datatrees import datatree, dtfield


class TestBasicXMLMapping(unittest.TestCase):
    """Test basic XML mapping functionality."""
    
    def setUp(self):
        """Set up basic classes for testing."""
        # Define field defaults for consistency
        self.DEFAULT_CONFIG = xfield(ftype=Attribute)

        @xdatatree
        class Person:
            XDATATREE_CONFIG = self.DEFAULT_CONFIG  # Sets default for all fields
            name: str = xfield(doc='Person name')
            age: int = xfield(doc='Person age') 
            address: str = xfield(ftype=TextElement, doc='Person address')  # Override default

        self.Person = Person

    def test_simple_person_creation(self):
        """Test creating a Person instance."""
        person = self.Person(name="John", age=30, address="123 Main St")
        self.assertEqual(person.name, "John")
        self.assertEqual(person.age, 30)
        self.assertEqual(person.address, "123 Main St")

    def test_person_serialization_spec(self):
        """Test creating serialization spec for Person."""
        spec = XmlSerializationSpec(self.Person, 'person')
        self.assertIsNotNone(spec)


class TestCollectionsAndLists(unittest.TestCase):
    """Test working with lists and collections."""
    
    def setUp(self):
        """Set up classes for collections testing."""
        DEFAULT_CONFIG = xfield(ftype=Attribute)

        @xdatatree
        class Person:
            XDATATREE_CONFIG = DEFAULT_CONFIG
            name: str = xfield(doc='Person name')
            age: int = xfield(doc='Person age') 
            address: str = xfield(ftype=TextElement, doc='Person address')

        @xdatatree
        class People:
            XDATATREE_CONFIG = xfield(ftype=Element)  # Default to elements
            people: List[Person] = xfield(doc='List of people')
            count: int = xfield(ftype=Attribute, doc='Total count')

        self.Person = Person
        self.People = People

    def test_people_creation(self):
        """Test creating People with list of Person objects."""
        people = self.People(
            count=2,
            people=[
                self.Person(name="John", age=30, address="123 Main St"),
                self.Person(name="Jane", age=25, address="456 Oak Ave")
            ]
        )
        self.assertEqual(people.count, 2)
        self.assertEqual(len(people.people), 2)
        self.assertEqual(people.people[0].name, "John")
        self.assertEqual(people.people[1].name, "Jane")


class TestSerializationDeserialization(unittest.TestCase):
    """Test complete serialization and deserialization workflow."""
    
    def setUp(self):
        """Set up classes and serialization spec."""
        DEFAULT_CONFIG = xfield(ftype=Attribute)

        @xdatatree
        class Person:
            XDATATREE_CONFIG = DEFAULT_CONFIG
            name: str = xfield(doc='Person name')
            age: int = xfield(doc='Person age') 
            address: str = xfield(ftype=TextElement, doc='Person address')

        @xdatatree
        class People:
            XDATATREE_CONFIG = xfield(ftype=Element)
            people: List[Person] = xfield(doc='List of people')
            count: int = xfield(ftype=Attribute, doc='Total count')

        self.Person = Person
        self.People = People
        
        # Create serialization specification
        self.SERIALIZATION_SPEC = XmlSerializationSpec(
            People,        # Root class
            'people',      # Root element name
            xml_namespaces=None  # Optional XML namespaces
        )

    def test_deserialize_from_xml(self):
        """Test deserializing from XML string."""
        xml_string = '''
        <people count="1">
            <people name="Alice" age="28">
                <address>789 Pine Rd</address>
            </people>
        </people>
        '''
        
        xml_tree = ET.fromstring(xml_string)
        people_obj, status = self.SERIALIZATION_SPEC.deserialize(xml_tree)
        
        self.assertEqual(people_obj.count, 1)
        self.assertEqual(people_obj.people[0].name, "Alice")
        self.assertEqual(people_obj.people[0].age, 28)
        self.assertEqual(people_obj.people[0].address, "789 Pine Rd")

    def test_serialize_to_xml(self):
        """Test serializing to XML."""
        people = self.People(
            count=1,
            people=[self.Person(name="Alice", age=28, address="789 Pine Rd")]
        )
        
        xml_element = self.SERIALIZATION_SPEC.serialize(people)
        xml_string = ET.tostring(xml_element, encoding='unicode')
        
        # Parse the generated XML to verify structure
        parsed = ET.fromstring(xml_string)
        self.assertEqual(parsed.tag, 'people')
        self.assertEqual(parsed.get('count'), '1')
        
        people_elem = parsed.find('people')
        self.assertIsNotNone(people_elem)
        self.assertEqual(people_elem.get('name'), 'Alice')
        self.assertEqual(people_elem.get('age'), '28')
        
        address_elem = people_elem.find('address')
        self.assertIsNotNone(address_elem)
        self.assertEqual(address_elem.text, '789 Pine Rd')

    def test_roundtrip_serialization(self):
        """Test roundtrip serialization/deserialization."""
        original = self.People(
            count=2,
            people=[
                self.Person(name="John", age=30, address="123 Main St"),
                self.Person(name="Jane", age=25, address="456 Oak Ave")
            ]
        )
        
        # Serialize
        xml_element = self.SERIALIZATION_SPEC.serialize(original)
        
        # Deserialize
        restored, status = self.SERIALIZATION_SPEC.deserialize(xml_element)
        
        # Verify
        self.assertEqual(restored.count, original.count)
        self.assertEqual(len(restored.people), len(original.people))
        
        for orig_person, restored_person in zip(original.people, restored.people):
            self.assertEqual(orig_person.name, restored_person.name)
            self.assertEqual(orig_person.age, restored_person.age)
            self.assertEqual(orig_person.address, restored_person.address)


class TestFieldTypes(unittest.TestCase):
    """Test different field types (Attribute, Element, Metadata)."""
    
    def test_attribute_fields(self):
        """Test fields mapped to XML attributes."""
        @xdatatree
        class Product:
            id: str = xfield(ftype=Attribute)
            price: float = xfield(ftype=Attribute)

        product = Product(id="ABC123", price=29.99)
        self.assertEqual(product.id, "ABC123")
        self.assertEqual(product.price, 29.99)
        
        # Test serialization
        spec = XmlSerializationSpec(Product, 'product')
        xml_element = spec.serialize(product)
        
        self.assertEqual(xml_element.get('id'), 'ABC123')
        self.assertEqual(xml_element.get('price'), '29.99')

    def test_element_fields(self):
        """Test fields mapped to child XML elements."""
        @xdatatree
        class Product:
            name: str = xfield(ftype=TextElement)
            description: str = xfield(ftype=TextElement)

        product = Product(name="Widget", description="A useful widget")
        
        spec = XmlSerializationSpec(Product, 'product')
        xml_element = spec.serialize(product)
        
        name_elem = xml_element.find('name')
        desc_elem = xml_element.find('description')
        
        self.assertIsNotNone(name_elem)
        self.assertIsNotNone(desc_elem)
        self.assertEqual(name_elem.text, 'Widget')
        self.assertEqual(desc_elem.text, 'A useful widget')

    def test_metadata_fields(self):
        """Test fields mapped to metadata elements."""
        @xdatatree
        class Product:
            category: str = xfield(ftype=Metadata)

        product = Product(category="electronics")
        
        spec = XmlSerializationSpec(Product, 'product')
        xml_element = spec.serialize(product)
        
        metadata_elem = xml_element.find('metadata[@key="category"]')
        self.assertIsNotNone(metadata_elem)
        self.assertEqual(metadata_elem.get('value'), 'electronics')

    def test_simple_types_as_elements(self):
        """Test that simple types (str, int, float, bool) are serialized as element text content."""
        @xdatatree
        class DataTypes:
            text_field: str = xfield(ftype=TextElement)
            number_field: int = xfield(ftype=TextElement)
            float_field: float = xfield(ftype=TextElement)
            bool_field: bool = xfield(ftype=TextElement)

        data = DataTypes(
            text_field="Hello World",
            number_field=42,
            float_field=3.14,
            bool_field=True
        )

        spec = XmlSerializationSpec(DataTypes, 'data')
        xml_element = spec.serialize(data)

        # Verify text content of elements
        text_elem = xml_element.find('text_field')
        self.assertIsNotNone(text_elem)
        self.assertEqual(text_elem.text, 'Hello World')

        number_elem = xml_element.find('number_field')
        self.assertIsNotNone(number_elem)
        self.assertEqual(number_elem.text, '42')

        float_elem = xml_element.find('float_field')
        self.assertIsNotNone(float_elem)
        self.assertEqual(float_elem.text, '3.14')

        bool_elem = xml_element.find('bool_field')
        self.assertIsNotNone(bool_elem)
        self.assertEqual(bool_elem.text, 'True')

    def test_simple_types_roundtrip(self):
        """Test roundtrip serialization/deserialization of simple types in elements."""
        @xdatatree
        class DataTypes:
            text_field: str = xfield(ftype=TextElement)
            number_field: int = xfield(ftype=TextElement)
            float_field: float = xfield(ftype=TextElement)
            bool_field: bool = xfield(ftype=TextElement)

        original = DataTypes(
            text_field="Test String",
            number_field=123,
            float_field=2.71,
            bool_field=False
        )
        
        spec = XmlSerializationSpec(DataTypes, 'data')
        
        # Serialize
        xml_element = spec.serialize(original)
        
        # Deserialize
        restored, status = spec.deserialize(xml_element)
        
        # Verify values are preserved
        self.assertEqual(restored.text_field, original.text_field)
        self.assertEqual(restored.number_field, original.number_field)
        self.assertEqual(restored.float_field, original.float_field)
        self.assertEqual(restored.bool_field, original.bool_field)

    def test_none_values_in_elements(self):
        """Test that None values in elements are handled gracefully."""
        @xdatatree
        class OptionalFields:
            optional_text: str = xfield(ftype=TextElement)
            optional_number: int = xfield(ftype=TextElement)

        # Test with None values
        data_with_none = OptionalFields(optional_text=None, optional_number=None)
        
        spec = XmlSerializationSpec(OptionalFields, 'optional')
        xml_element = spec.serialize(data_with_none)
        
        # None values should not create elements
        text_elem = xml_element.find('optional_text')
        number_elem = xml_element.find('optional_number')
        
        self.assertIsNone(text_elem)
        self.assertIsNone(number_elem)


class TestCustomConverters(unittest.TestCase):
    """Test custom converters for complex types."""
    
    def setUp(self):
        """Set up custom converter classes."""
        @datatree
        class MatrixConverter:
            """Convert between space-separated string and 4x4 matrix."""
            matrix: np.ndarray = dtfield(doc='4x4 transformation matrix')

            def __init__(self, matrix_input: Union[str, np.ndarray]):
                if isinstance(matrix_input, np.ndarray):
                    self.matrix = matrix_input
                else:
                    # Parse "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1" format
                    values = [float(x) for x in re.split(r'\s+', matrix_input.strip())]
                    if len(values) != 16:
                        raise ValueError(f"Expected 16 values, got {len(values)}")
                    self.matrix = np.array(values).reshape((4, 4))

            def __str__(self):
                return ' '.join(str(x) for x in self.matrix.flatten())

        @xdatatree
        class Transform:
            XDATATREE_CONFIG = xfield(ftype=Metadata)
            id: str = xfield(ftype=Attribute, doc='Transform ID')
            matrix: MatrixConverter = xfield(doc='Transformation matrix')

        self.MatrixConverter = MatrixConverter
        self.Transform = Transform

    def test_matrix_converter_from_string(self):
        """Test creating matrix converter from string."""
        matrix_str = "1 0 0 5 0 1 0 10 0 0 1 0 0 0 0 1"
        converter = self.MatrixConverter(matrix_str)
        
        expected = np.array([
            [1, 0, 0, 5],
            [0, 1, 0, 10],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        
        np.testing.assert_array_equal(converter.matrix, expected)

    def test_matrix_converter_from_array(self):
        """Test creating matrix converter from numpy array."""
        matrix_array = np.eye(4)
        converter = self.MatrixConverter(matrix_array)
        
        np.testing.assert_array_equal(converter.matrix, matrix_array)

    def test_matrix_converter_str(self):
        """Test string representation of matrix converter."""
        matrix_array = np.eye(4)
        converter = self.MatrixConverter(matrix_array)
        
        result = str(converter)
        expected = "1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0 0.0 0.0 0.0 0.0 1.0"
        self.assertEqual(result, expected)

    def test_transform_with_converter(self):
        """Test Transform class using MatrixConverter."""
        transform = self.Transform(
            id="T1",
            matrix=self.MatrixConverter("1 0 0 5 0 1 0 10 0 0 1 0 0 0 0 1")
        )
        
        self.assertEqual(transform.id, "T1")
        self.assertIsInstance(transform.matrix, self.MatrixConverter)
        
        expected_matrix = np.array([
            [1, 0, 0, 5],
            [0, 1, 0, 10],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])
        np.testing.assert_array_equal(transform.matrix.matrix, expected_matrix)


class TestXMLNamespaces(unittest.TestCase):
    """Test XML namespace handling."""
    
    def setUp(self):
        """Set up namespace classes."""
        # Define namespaces
        self.NAMESPACES = XmlNamespaces(
            xmlns="http://schemas.example.com/model/2023",
            geom="http://schemas.example.com/geometry/2023",
            mat="http://schemas.example.com/materials/2023"
        )

        @xdatatree
        class Component:
            XDATATREE_CONFIG = xfield(xmlns=self.NAMESPACES.xmlns, ftype=Attribute)
            
            id: str = xfield(doc='Component ID')
            geometry_ref: str = xfield(xmlns=self.NAMESPACES.geom, doc='Geometry reference')
            material_id: str = xfield(xmlns=self.NAMESPACES.mat, doc='Material ID')

        self.Component = Component
        
        # Create specification with namespaces
        self.SERIALIZATION_SPEC = XmlSerializationSpec(
            Component,
            'component',
            xml_namespaces=self.NAMESPACES
        )

    def test_component_creation(self):
        """Test creating component with namespace fields."""
        component = self.Component(
            id="C001",
            geometry_ref="G001",
            material_id="M001"
        )
        
        self.assertEqual(component.id, "C001")
        self.assertEqual(component.geometry_ref, "G001")
        self.assertEqual(component.material_id, "M001")

    def test_namespace_serialization(self):
        """Test serialization with namespaces."""
        component = self.Component(
            id="C001",
            geometry_ref="G001",
            material_id="M001"
        )
        
        xml_element = self.SERIALIZATION_SPEC.serialize(component)
        xml_string = ET.tostring(xml_element, encoding='unicode')
        
        # Verify namespaces are present (with auto-generated prefixes)
        self.assertIn('xmlns:ns0=', xml_string)  # Default namespace gets a prefix
        self.assertIn('xmlns:ns1=', xml_string)  # geom namespace
        self.assertIn('xmlns:ns2=', xml_string)  # mat namespace
        
        # Verify the namespace URIs are correct
        self.assertIn('http://schemas.example.com/model/2023', xml_string)
        self.assertIn('http://schemas.example.com/geometry/2023', xml_string)
        self.assertIn('http://schemas.example.com/materials/2023', xml_string)
        
        # Verify attributes are namespaced correctly
        self.assertIn('ns0:id="C001"', xml_string)
        self.assertIn('ns1:geometry_ref="G001"', xml_string)
        self.assertIn('ns2:material_id="M001"', xml_string)


class TestNameTransformations(unittest.TestCase):
    """Test name transformation functionality."""
    
    def test_snake_camel_conversion(self):
        """Test converting snake_case to camelCase."""
        @xdatatree
        class APIResponse:
            XDATATREE_CONFIG = xfield(
                ename_transform=CamelSnakeConverter,    # element names: snake_case → camelCase
                aname_transform=SnakeCamelConverter,    # attribute names: snake_case → camelCase
                ftype=Attribute
            )
            
            user_id: str = xfield(doc='User identifier')        # becomes userId attribute
            creation_date: str = xfield(ftype=TextElement, doc='Creation date')  # becomes creationDate element

        response = APIResponse(user_id="123", creation_date="2023-01-01")
        self.assertEqual(response.user_id, "123")
        self.assertEqual(response.creation_date, "2023-01-01")
        
        # Test serialization produces correct names
        spec = XmlSerializationSpec(APIResponse, 'response')
        xml_element = spec.serialize(response)
        
        # Check transformed attribute name
        self.assertIsNotNone(xml_element.get('UserId'))
        # Check transformed element name
        creation_elem = xml_element.find('creation_date')
        self.assertIsNotNone(creation_elem)


class TestCustomValueCollectors(unittest.TestCase):
    """Test custom value collectors."""
    
    def setUp(self):
        """Set up value collector classes."""
        @xdatatree
        class Triangle:
            v1: int = xfield(ftype=Attribute, doc='First vertex index')
            v2: int = xfield(ftype=Attribute, doc='Second vertex index') 
            v3: int = xfield(ftype=Attribute, doc='Third vertex index')
            color: str = xfield(ftype=Attribute, doc='Triangle color')

        @datatree
        class TriangleCollector(ValueCollector):
            """Collect triangles into optimized numpy arrays."""
            vertices: List[np.ndarray] = dtfield(default_factory=list, doc='Vertex indices')
            colors: List[str] = dtfield(default_factory=list, doc='Triangle colors')
            
            CONTAINED_TYPE = Triangle
            
            def append(self, triangle: Triangle):
                if not isinstance(triangle, Triangle):
                    raise ValueError(f'Expected Triangle, got {type(triangle).__name__}')
                self.vertices.append(np.array([triangle.v1, triangle.v2, triangle.v3]))
                self.colors.append(triangle.color)

            def get(self) -> Tuple[np.ndarray, List[str]]:
                """Return optimized representation."""
                return np.array(self.vertices), self.colors
            
            @classmethod
            def to_contained_type(cls, data: Tuple[np.ndarray, List[str]]):
                """Convert back to Triangle objects for serialization."""
                vertices, colors = data
                for vertex_trio, color in zip(vertices, colors):
                    yield Triangle(v1=vertex_trio[0], v2=vertex_trio[1], v3=vertex_trio[2], color=color)

        @xdatatree  
        class Mesh:
            triangles: TriangleCollector = xfield(ftype=Element, doc='Mesh triangles')

        self.Triangle = Triangle
        self.TriangleCollector = TriangleCollector
        self.Mesh = Mesh

    def test_triangle_collector_creation(self):
        """Test creating and using triangle collector."""
        collector = self.TriangleCollector()
        
        triangle1 = self.Triangle(v1=0, v2=1, v3=2, color="red")
        triangle2 = self.Triangle(v1=1, v2=2, v3=3, color="blue")
        
        collector.append(triangle1)
        collector.append(triangle2)
        
        vertices, colors = collector.get()
        
        expected_vertices = np.array([[0, 1, 2], [1, 2, 3]])
        np.testing.assert_array_equal(vertices, expected_vertices)
        self.assertEqual(colors, ["red", "blue"])

    def test_triangle_collector_type_validation(self):
        """Test triangle collector validates input types."""
        collector = self.TriangleCollector()
        
        with self.assertRaises(ValueError):
            collector.append("not a triangle")

    def test_triangle_collector_conversion(self):
        """Test converting back to Triangle objects."""
        vertices = np.array([[0, 1, 2], [1, 2, 3]])
        colors = ["red", "blue"]
        data = (vertices, colors)
        
        triangles = list(self.TriangleCollector.to_contained_type(data))
        
        self.assertEqual(len(triangles), 2)
        self.assertEqual(triangles[0].v1, 0)
        self.assertEqual(triangles[0].v2, 1)
        self.assertEqual(triangles[0].v3, 2)
        self.assertEqual(triangles[0].color, "red")
        
        self.assertEqual(triangles[1].v1, 1)
        self.assertEqual(triangles[1].v2, 2)
        self.assertEqual(triangles[1].v3, 3)
        self.assertEqual(triangles[1].color, "blue")


class TestErrorHandlingAndValidation(unittest.TestCase):
    """Test error handling and validation features."""
    
    def setUp(self):
        """Set up classes for error testing."""
        @xdatatree
        class SimpleClass:
            value: str = xfield(ftype=Attribute)

        self.SimpleClass = SimpleClass

    def test_parser_options_creation(self):
        """Test creating parser options."""
        strict_options = XmlParserOptions(
            assert_unused_elements=True,     # Raise error for unknown elements
            assert_unused_attributes=True,   # Raise error for unknown attributes
            print_unused_elements=True       # Print warnings for debugging
        )
        
        spec = XmlSerializationSpec(
            self.SimpleClass,
            'root',
            options=strict_options
        )
        
        self.assertIsNotNone(spec)

    def test_status_checking(self):
        """Test checking deserialization status."""
        spec = XmlSerializationSpec(self.SimpleClass, 'simple')
        xml_string = '<simple value="test"/>'
        xml_tree = ET.fromstring(xml_string)
        
        model, status = spec.deserialize(xml_tree)
        
        # Should have no unknown elements or attributes for this simple case
        self.assertFalse(status.contains_unknown_elements)
        self.assertFalse(status.contains_unknown_attributes)

    def test_error_type_imports(self):
        """Test that error types can be imported and used."""
        # Just verify the error types are available
        self.assertTrue(hasattr(TooManyValuesError, '__name__'))


class TestComplete3DModelExample(unittest.TestCase):
    """Test the complete 3D model serialization example."""
    
    def setUp(self):
        """Set up the complete 3D model example classes."""
        # Define namespaces
        self.NAMESPACES = XmlNamespaces(
            xmlns="http://schemas.example.com/3d/2023",
            material="http://schemas.example.com/materials/2023"
        )

        # Field defaults
        DEFAULT_CONFIG = xfield(xmlns=self.NAMESPACES.xmlns, ftype=Attribute)

        @xdatatree
        class Vertex:
            XDATATREE_CONFIG = DEFAULT_CONFIG
            x: float = xfield(doc='X coordinate')
            y: float = xfield(doc='Y coordinate') 
            z: float = xfield(doc='Z coordinate')

        @xdatatree
        class Triangle:
            XDATATREE_CONFIG = DEFAULT_CONFIG
            v1: int = xfield(doc='First vertex index')
            v2: int = xfield(doc='Second vertex index')
            v3: int = xfield(doc='Third vertex index')

        @xdatatree
        class Material:
            XDATATREE_CONFIG = xfield(xmlns=self.NAMESPACES.material, ftype=Attribute)
            id: str = xfield(doc='Material identifier')
            name: str = xfield(doc='Material name')
            color: str = xfield(doc='Material color (hex)')

        @xdatatree
        class Mesh:
            XDATATREE_CONFIG = xfield(xmlns=self.NAMESPACES.xmlns, ftype=Element)
            vertices: List[Vertex] = xfield(doc='Mesh vertices')
            triangles: List[Triangle] = xfield(doc='Mesh triangles')
            material_id: str = xfield(ftype=Attribute, doc='Associated material')

        @xdatatree
        class Model:
            XDATATREE_CONFIG = xfield(xmlns=self.NAMESPACES.xmlns, ftype=Element)
            name: str = xfield(ftype=Attribute, doc='Model name')
            materials: List[Material] = xfield(doc='Available materials')
            meshes: List[Mesh] = xfield(doc='Model meshes')

        self.Vertex = Vertex
        self.Triangle = Triangle
        self.Material = Material
        self.Mesh = Mesh
        self.Model = Model

        # Create serialization spec
        self.SPEC = XmlSerializationSpec(
            Model,
            'model',
            xml_namespaces=self.NAMESPACES,
            options=XmlParserOptions(assert_unused_elements=True)
        )

    def test_create_complete_model(self):
        """Test creating the complete 3D model."""
        model = self.Model(
            name="Simple Cube",
            materials=[
                self.Material(id="mat1", name="Red Plastic", color="#FF0000")
            ],
            meshes=[
                self.Mesh(
                    material_id="mat1",
                    vertices=[
                        self.Vertex(x=0.0, y=0.0, z=0.0),
                        self.Vertex(x=1.0, y=0.0, z=0.0),
                        self.Vertex(x=1.0, y=1.0, z=0.0),
                        self.Vertex(x=0.0, y=1.0, z=0.0),
                    ],
                    triangles=[
                        self.Triangle(v1=0, v2=1, v3=2),
                        self.Triangle(v1=0, v2=2, v3=3),
                    ]
                )
            ]
        )
        
        # Verify model structure
        self.assertEqual(model.name, "Simple Cube")
        self.assertEqual(len(model.materials), 1)
        self.assertEqual(model.materials[0].id, "mat1")
        self.assertEqual(len(model.meshes), 1)
        self.assertEqual(len(model.meshes[0].vertices), 4)
        self.assertEqual(len(model.meshes[0].triangles), 2)

    def test_serialize_complete_model(self):
        """Test serializing the complete 3D model."""
        model = self.Model(
            name="Simple Cube",
            materials=[
                self.Material(id="mat1", name="Red Plastic", color="#FF0000")
            ],
            meshes=[
                self.Mesh(
                    material_id="mat1",
                    vertices=[
                        self.Vertex(x=0.0, y=0.0, z=0.0),
                        self.Vertex(x=1.0, y=0.0, z=0.0),
                    ],
                    triangles=[
                        self.Triangle(v1=0, v2=1, v3=2),
                    ]
                )
            ]
        )
        
        # Serialize to XML
        xml_element = self.SPEC.serialize(model)
        xml_string = ET.tostring(xml_element, encoding='unicode')
        
        # Verify XML contains expected content
        self.assertIn('name="Simple Cube"', xml_string)
        self.assertIn('id="mat1"', xml_string)
        self.assertIn('material_id="mat1"', xml_string)

    def test_roundtrip_complete_model(self):
        """Test roundtrip serialization/deserialization of complete model."""
        original_model = self.Model(
            name="Test Cube",
            materials=[
                self.Material(id="mat1", name="Red Plastic", color="#FF0000")
            ],
            meshes=[
                self.Mesh(
                    material_id="mat1",
                    vertices=[
                        self.Vertex(x=0.0, y=0.0, z=0.0),
                        self.Vertex(x=1.0, y=0.0, z=0.0),
                    ],
                    triangles=[
                        self.Triangle(v1=0, v2=1, v3=2),
                    ]
                )
            ]
        )
        
        # Serialize
        xml_element = self.SPEC.serialize(original_model)
        
        # Deserialize
        restored_model, status = self.SPEC.deserialize(xml_element)
        
        # Verify roundtrip accuracy
        self.assertEqual(restored_model.name, original_model.name)
        self.assertEqual(len(restored_model.materials), len(original_model.materials))
        self.assertEqual(restored_model.materials[0].id, original_model.materials[0].id)
        self.assertEqual(restored_model.materials[0].name, original_model.materials[0].name)
        self.assertEqual(restored_model.materials[0].color, original_model.materials[0].color)
        
        self.assertEqual(len(restored_model.meshes), len(original_model.meshes))
        self.assertEqual(restored_model.meshes[0].material_id, original_model.meshes[0].material_id)
        
        # Verify vertices
        orig_vertices = original_model.meshes[0].vertices
        restored_vertices = restored_model.meshes[0].vertices
        self.assertEqual(len(restored_vertices), len(orig_vertices))
        
        for orig_v, restored_v in zip(orig_vertices, restored_vertices):
            self.assertEqual(orig_v.x, restored_v.x)
            self.assertEqual(orig_v.y, restored_v.y)
            self.assertEqual(orig_v.z, restored_v.z)
        
        # Verify triangles
        orig_triangles = original_model.meshes[0].triangles
        restored_triangles = restored_model.meshes[0].triangles
        self.assertEqual(len(restored_triangles), len(orig_triangles))
        
        for orig_t, restored_t in zip(orig_triangles, restored_triangles):
            self.assertEqual(orig_t.v1, restored_t.v1)
            self.assertEqual(orig_t.v2, restored_t.v2)
            self.assertEqual(orig_t.v3, restored_t.v3)


if __name__ == '__main__':
    unittest.main()
