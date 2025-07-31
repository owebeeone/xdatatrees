# XDataTrees

A datatrees wrapper for creating XML serializers and deserializers with automatic field mapping, type conversion, and namespace support.

XDataTrees extends Python's dataclasses through datatrees to provide a clean, declarative API for mapping between XML documents and Python objects. It eliminates the boilerplate code typically required for XML serialization/deserialization while providing type safety and comprehensive error handling.

## Installation

```bash
pip install xdatatrees
```

## Documentation

This README provides a quick-start guide with basic usage examples.

For a comprehensive guide covering advanced topics, best practices, and detailed explanations of all features, please refer to the **[Full Documentation](DOCUMENTATION.md)**.

## Core Features

- **Declarative XML Mapping**: Map Python classes to XML using simple annotations
- **Automatic Type Conversion**: Built-in conversion between Python types and XML string representations
- **Flexible Field Types**: Support for XML attributes, elements, and metadata
- **Namespace Support**: Full XML namespace handling with automatic prefix management
- **Custom Converters**: Extensible system for complex data type transformations
- **Value Collectors**: Specialized handling for collections and custom aggregations
- **Comprehensive Error Handling**: Detailed error reporting with unused element/attribute detection
- **Name Transformations**: Automatic conversion between naming conventions (camelCase ↔ snake_case)

## Why XDataTrees?

### The Challenge of XML Processing

Traditional XML processing in Python often requires verbose, error-prone code:

```python
# Without XDataTrees - manual XML processing
import xml.etree.ElementTree as ET

def parse_person_xml(xml_string):
    root = ET.fromstring(xml_string)
    person = {
        'name': root.get('name'),
        'age': int(root.get('age')),
        'address': root.find('address').text if root.find('address') is not None else None
    }
    return person

def create_person_xml(person):
    root = ET.Element('person')
    root.set('name', person['name'])
    root.set('age', str(person['age']))
    if person.get('address'):
        addr_elem = ET.SubElement(root, 'address')
        addr_elem.text = person['address']
    return ET.tostring(root, encoding='unicode')
```

This approach has several problems:
- Manual type conversion and validation
- No clear mapping between XML structure and Python objects
- Error-prone attribute and element handling
- No namespace support
- Difficult to maintain as XML schema evolves

### XDataTrees: Declarative XML Processing

XDataTrees provides a clean, maintainable pattern:

```python
# With XDataTrees - declarative and type-safe
from xdatatrees import xdatatree, xfield, Attribute, TextElement

@xdatatree
class Person:
    name: str = xfield(ftype=Attribute, doc='Person name')
    age: int = xfield(ftype=Attribute, doc='Person age')
    address: str = xfield(ftype=TextElement, doc='Person address')

# Automatic serialization/deserialization with full type safety
# Usage shown in examples below
```

### Benefits

1. **Type Safety**: Automatic conversion with validation
2. **Clear Schema Definition**: The class structure documents the XML schema
3. **Maintainable**: Changes to XML structure require minimal code changes
4. **Namespace Aware**: Built-in support for complex XML namespaces
5. **Error Handling**: Comprehensive validation and error reporting
6. **Extensible**: Custom converters for complex data types

## Basic Usage

### 1. Simple XML Mapping

```python
from xdatatrees import xdatatree, xfield, Attribute, TextElement
from typing import List

# Define field defaults for consistency
DEFAULT_CONFIG = xfield(ftype=Attribute)

@xdatatree
class Person:
    XDATATREE_CONFIG = DEFAULT_CONFIG  # Sets default for all fields
    name: str = xfield(doc='Person name')
    age: int = xfield(doc='Person age') 
    address: str = xfield(ftype=TextElement, doc='Person address')  # Override default

# This maps to XML like:
# <person name="John" age="30">
#   <address>123 Main St</address>
# </person>
```

### 2. Working with Lists and Collections

```python
from xdatatrees import Element

@xdatatree
class People:
    XDATATREE_CONFIG = xfield(ftype=Element)  # Default to elements
    people: List[Person] = xfield(doc='List of people')
    count: int = xfield(ftype=Attribute, doc='Total count')

# Maps to:
# <people count="2">
#   <people name="John" age="30"><address>123 Main St</address></people>
#   <people name="Jane" age="25"><address>456 Oak Ave</address></people>
# </people>
```

### 3. Serialization and Deserialization

```python
from xdatatrees import XmlSerializationSpec
import xml.etree.ElementTree as ET

# Create serialization specification
SERIALIZATION_SPEC = XmlSerializationSpec(
    People,        # Root class
    'people',      # Root element name
    xml_namespaces=None  # Optional XML namespaces
)

# Deserialize from XML
xml_string = '''
<people count="1">
    <people name="Alice" age="28">
        <address>789 Pine Rd</address>
    </people>
</people>
'''

xml_tree = ET.fromstring(xml_string)
people_obj, status = SERIALIZATION_SPEC.deserialize(xml_tree)

print(f"Count: {people_obj.count}")  # 1
print(f"First person: {people_obj.people[0].name}")  # Alice

# Serialize back to XML
xml_element = SERIALIZATION_SPEC.serialize(people_obj)
xml_string = ET.tostring(xml_element, encoding='unicode')
```

## Field Types

XDataTrees supports four main field mapping types:

### Attribute Fields
Map to XML attributes on the element:
```python
from xdatatrees import xdatatree, xfield, Attribute

@xdatatree
class Product:
    id: str = xfield(ftype=Attribute)
    price: float = xfield(ftype=Attribute)

# <product id="ABC123" price="29.99"/>
```

### Element Fields  
Map to child XML elements containing nested xdatatree classes:
```python
from xdatatrees import Element

@xdatatree
class Address:
    street: str = xfield(ftype=Attribute)
    city: str = xfield(ftype=Attribute)

@xdatatree
class Person:
    name: str = xfield(ftype=Attribute)
    address: Address = xfield(ftype=Element)

# <person name="John">
#   <address street="123 Main St" city="Anytown"/>
# </person>
```

### TextElement Fields
Map to XML elements containing only simple text content (str, int, float, bool):
```python
from xdatatrees import xdatatree, xfield, TextElement

@xdatatree
class Product:
    name: str = xfield(ftype=TextElement)
    price: float = xfield(ftype=TextElement)
    in_stock: bool = xfield(ftype=TextElement)

# <product>
#   <name>Widget</name>
#   <price>29.99</price>
#   <in_stock>true</in_stock>
# </product>
```

### Metadata Fields
Map to special metadata elements with key-value structure:
```python
from xdatatrees import Metadata

@xdatatree
class Product:
    category: str = xfield(ftype=Metadata)

# <product>
#   <metadata key="category" value="electronics"/>
# </product>
```

## Advanced Features

### 1. Custom Converters for Complex Types

For data types that need special handling, create custom converter classes:

```python
from xdatatrees import xdatatree, xfield, Attribute, Metadata
from datatrees import datatree, dtfield
import numpy as np
import re
from typing import Union

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

# Usage:
# <transform id="T1">
#   <metadata key="matrix" value="1 0 0 5 0 1 0 10 0 0 1 0 0 0 0 1"/>
# </transform>
```

### 2. XML Namespaces

Handle complex XML documents with multiple namespaces:

```python
from xdatatrees import xdatatree, xfield, Attribute, XmlNamespaces, XmlSerializationSpec

# Define namespaces
NAMESPACES = XmlNamespaces(
    xmlns="http://schemas.example.com/model/2023",
    geom="http://schemas.example.com/geometry/2023",
    mat="http://schemas.example.com/materials/2023"
)

@xdatatree
class Component:
    XDATATREE_CONFIG = xfield(xmlns=NAMESPACES.xmlns, ftype=Attribute)
    
    id: str = xfield(doc='Component ID')
    geometry_ref: str = xfield(xmlns=NAMESPACES.geom, doc='Geometry reference')
    material_id: str = xfield(xmlns=NAMESPACES.mat, doc='Material ID')

# Create specification with namespaces
SERIALIZATION_SPEC = XmlSerializationSpec(
    Component,
    'component',
    xml_namespaces=NAMESPACES
)

# Handles XML like:
# <component xmlns="http://schemas.example.com/model/2023"
#           xmlns:geom="http://schemas.example.com/geometry/2023" 
#           xmlns:mat="http://schemas.example.com/materials/2023"
#           id="C001" 
#           geom:geometry_ref="G001"
#           mat:material_id="M001"/>
```

### 3. Name Transformations

Automatically convert between naming conventions:

```python
from xdatatrees import xdatatree, xfield, Attribute, TextElement, CamelSnakeConverter, SnakeCamelConverter

@xdatatree
class APIResponse:
    XDATATREE_CONFIG = xfield(
        ename_transform=CamelSnakeConverter,    # element names: snake_case → camelCase
        aname_transform=SnakeCamelConverter,    # attribute names: snake_case → camelCase
        ftype=Attribute
    )
    
    user_id: str = xfield(doc='User identifier')        # becomes UserId attribute
    creation_date: str = xfield(ftype=TextElement, doc='Creation date')  # becomes creation_date element

# Python field: user_id → XML attribute: UserId
# Python field: creation_date → XML element: creation_date
```

### 4. Custom Value Collectors

For specialized collection handling and data aggregation:

```python
from xdatatrees import ValueCollector, Element
from typing import List, Tuple

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

# The collector automatically handles:
# - Parsing multiple <triangle> elements into optimized arrays
# - Converting back to individual Triangle objects for serialization
# - Providing efficient access to the aggregated data
```

## Error Handling and Validation

XDataTrees provides comprehensive error handling and validation:

### 1. Parser Options

Control parsing behavior and error reporting:

```python
from xdatatrees import XmlParserOptions, XmlSerializationSpec

# Strict parsing - fail on unknown elements/attributes
strict_options = XmlParserOptions(
    assert_unused_elements=True,     # Raise error for unknown elements
    assert_unused_attributes=True,   # Raise error for unknown attributes
    print_unused_elements=True       # Print warnings for debugging
)

SERIALIZATION_SPEC = XmlSerializationSpec(
    MyClass,
    'root',
    options=strict_options
)
```

### 2. Handling Unknown XML Content

```python
# Deserialize with error checking
model, status = SERIALIZATION_SPEC.deserialize(xml_tree)

# Check for parsing issues
if status.contains_unknown_elements:
    print("Warning: Found unknown XML elements")
    # Access details through the model objects
    
if status.contains_unknown_attributes:
    print("Warning: Found unknown XML attributes")

# Examine specific nodes for unknown content
def check_unknown_content(node):
    if hasattr(node, 'contains_unknown_elements') and node.contains_unknown_elements:
        print(f'Node {node.__class__.__name__} has unknown elements:')
        print(node.xdatatree_unused_xml_elements)
        
    if hasattr(node, 'contains_unknown_attributes') and node.contains_unknown_attributes:
        print(f'Node {node.__class__.__name__} has unknown attributes:')
        print(node.xdatatree_unused_xml_attributes)
```

### 3. Common Error Types

XDataTrees provides specific error types for different failure modes:

```python
from xdatatrees import TooManyValuesError

try:
    model, status = SERIALIZATION_SPEC.deserialize(xml_tree)
except TooManyValuesError as e:
    print(f"Multiple values provided for single-value field: {e}")
except Exception as e:
    print(f"General parsing error: {e}")
```

## Best Practices

1. **Define XDATATREE_CONFIG**: Set common defaults to reduce repetition and improve consistency
   ```python
   DEFAULT_CONFIG = xfield(ftype=Attribute, ename_transform=CamelSnakeConverter)
   ```

2. **Use Descriptive Documentation**: Document all fields for better maintainability
   ```python
   name: str = xfield(doc='User full name (first and last)')
   ```

3. **Leverage Custom Converters**: Create reusable converters for complex data types
   
4. **Use Namespaces**: Always define and use XmlNamespaces for production XML schemas

5. **Handle Errors Gracefully**: Use appropriate parser options and error handling for your use case

6. **Type Annotations Matter**: XDataTrees uses type annotations for conversion - ensure they're accurate

7. **Validate Early**: Use strict parsing during development to catch schema mismatches

## Complete Example: 3D Model Serialization

Here's a comprehensive example showing XDataTrees in action:

<details>
<summary>Click to see the complete 3D model example</summary>

```python
from xdatatrees import xdatatree, xfield, Attribute, Element, Metadata
from xdatatrees import XmlSerializationSpec, XmlNamespaces, XmlParserOptions
from datatrees import datatree, dtfield
from typing import List
import xml.etree.ElementTree as ET

# Define namespaces
NAMESPACES = XmlNamespaces(
    xmlns="http://schemas.example.com/3d/2023",
    material="http://schemas.example.com/materials/2023"
)

# Field defaults
DEFAULT_CONFIG = xfield(xmlns=NAMESPACES.xmlns, ftype=Attribute)

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
    XDATATREE_CONFIG = xfield(xmlns=NAMESPACES.material, ftype=Attribute)
    id: str = xfield(doc='Material identifier')
    name: str = xfield(doc='Material name')
    color: str = xfield(doc='Material color (hex)')

@xdatatree
class Mesh:
    XDATATREE_CONFIG = xfield(xmlns=NAMESPACES.xmlns, ftype=Element)
    vertices: List[Vertex] = xfield(doc='Mesh vertices')
    triangles: List[Triangle] = xfield(doc='Mesh triangles')
    material_id: str = xfield(ftype=Attribute, doc='Associated material')

@xdatatree
class Model:
    XDATATREE_CONFIG = xfield(xmlns=NAMESPACES.xmlns, ftype=Element)
    name: str = xfield(ftype=Attribute, doc='Model name')
    materials: List[Material] = xfield(doc='Available materials')
    meshes: List[Mesh] = xfield(doc='Model meshes')

# Create serialization spec
SPEC = XmlSerializationSpec(
    Model,
    'model',
    xml_namespaces=NAMESPACES,
    options=XmlParserOptions(assert_unused_elements=True)
)

# Create a model
model = Model(
    name="Simple Cube",
    materials=[
        Material(id="mat1", name="Red Plastic", color="#FF0000")
    ],
    meshes=[
        Mesh(
            material_id="mat1",
            vertices=[
                Vertex(x=0.0, y=0.0, z=0.0),
                Vertex(x=1.0, y=0.0, z=0.0),
                Vertex(x=1.0, y=1.0, z=0.0),
                Vertex(x=0.0, y=1.0, z=0.0),
            ],
            triangles=[
                Triangle(v1=0, v2=1, v3=2),
                Triangle(v1=0, v2=2, v3=3),
            ]
        )
    ]
)

# Serialize to XML
xml_element = SPEC.serialize(model)
xml_string = ET.tostring(xml_element, encoding='unicode')
print("Generated XML:")
print(xml_string)

# Deserialize back
xml_tree = ET.fromstring(xml_string)
restored_model, status = SPEC.deserialize(xml_tree)

print(f"\nRestored model: {restored_model.name}")
print(f"Material count: {len(restored_model.materials)}")
print(f"Vertex count: {len(restored_model.meshes[0].vertices)}")
```
</details>

## Limitations

- **InitVar Support**: Dataclasses InitVar annotations are not currently supported
- **Circular References**: Circular object references are not handled automatically
- **Schema Validation**: XDataTrees focuses on serialization/deserialization, not XML schema validation

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the LGPLv2.1 - see the LICENSE file for details.

## Acknowledgments

XDataTrees was developed to meet anchorscad's need for robust 3MF file serialization and deserialization. It builds upon the datatrees library (also from the anchorscad project) to provide a comprehensive solution for XML processing with the full feature set of datatrees available through the xdatatree decorator.
