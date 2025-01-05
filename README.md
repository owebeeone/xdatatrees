# xdatatrees Documentation

A datatrees wrapper for creating XML serializers / deserializers. Via datatrees it extends Python's dataclasses to support XML to Python class mappings.

## Basic Usage

### 1. Creating an XML-mappable Class

To create a class that can be serialized to and deserialized from XML.

Note that the type annotation for the field is used to perform conversions, they're not just type hints.

```python
from anchorscad.xdatatrees import xdatatree, xfield, Attribute, Element, Metadata
# Define default configuration for fields, this is optional but recommended to
# make the code more readable and to avoid repeating the same parameters for each field.
DEFAULT_CONFIG = xfield(ename_transform=CamelSnakeConverter, ftype=Attribute)

# Define the class with the xdatatree decorator
@xdatatree
class Person:
    XDATATREE_CONFIG = DEFAULT_CONFIG # Sets the default configuration for all fields in the class.
    name: str = xfield(doc='Person name')
    age: int = xfield(doc='Person age')
    address: str = xfield(ftype=Element, doc='Person address')

@xdatatree
class People:
    XDATATREE_CONFIG = DEFAULT_CONFIG(ftype=Element) # Default ftype to Element for all fields in the class.
    people: List[Person] = xfield(doc='List of people')

```

### 2. Field Types

XDataTrees supports three main field types:

- `Attribute`: Maps to XML attributes
- `Element`: Maps to XML child elements
- `Metadata`: Maps to special metadata elements

Example:

```python
@xdatatree
class Product:
    # As an attribute: <product id="123">
    id: str = xfield(ftype=Attribute)
    # As an element: <product><name>Widget</name></product>
    name: str = xfield(ftype=Element)
    # As metadata: <metadata key="category" value="electronics"/>
    category: str = xfield(ftype=Metadata)
```

### 3. Lists and Complex Types

XDataTrees supports lists and nested objects:

```python
@xdatatree
class Order:
    XDATATREE_CONFIG = DEFAULT_CONFIG
    order_id: str = xfield(ftype=Attribute)
    items: List[Product] = xfield(ftype=Element, doc='List of products')
```

### 4. Custom Converters

For complex data types, you can create custom converters:

```python
@datatree
class MatrixConverter:
    '''Convert a 16 value string like "1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1" to a
    GMatrix and back.'''
    matrix: GMatrix = dtfield(doc='The matrix as a GMatrix')

    def __init__(self, matrix_str: Union[str, GMatrix]):
        if isinstance(matrix_str, GMatrix):
            self.matrix = matrix_str
        else:
            nparray = np.array([float(x) for x in re.split(r'\s+', matrix_str)])
            self.matrix = GMatrix(nparray.reshape((4, 4)))
    def __str__(self):
        return ' '.join([float_to_str(x) for x in self.matrix.A.flatten()])
    
    def __repr__(self):
        return self.__str__()

@xdatatree
class Part:
    XDATATREE_CONFIG=DEFAULT_CONFIG(ftype=Metadata)
    id: str = xfield(ftype=Attribute, doc='Id of the part')
    subtype: str = xfield(ftype=Attribute, doc='Subtype of the part')
    name: str = xfield(ftype=Metadata, doc='Name of the part')
    matrix: MatrixConverter = xfield(ftype=Metadata, doc='Frame of ref of the object')      
```

### 5. Serialization and Deserialization

To serialize/deserialize objects:

```python
from anchorscad.xdatatrees import serialize, deserialize, XmlSerializationSpec
# Create a serialization specification
SERIALIZATION_SPEC = XmlSerializationSpec(
    Model, # Your root class
    'model', # Root element name
    namespaces # Optional XML namespaces
)
# Deserialize from XML
xml_tree = etree.fromstring(xml_string)
model, status = SERIALIZATION_SPEC.deserialize(xml_tree)

#Serialize to XML
xml_element = SERIALIZATION_SPEC.serialize(model)
```
## Advanced Features

### 1. Name Transformations

XDataTrees provides converters for naming conventions:

```python
# Convert between camelCase and snake_case

DEFAULT_CONFIG = xfield(
    ename_transform=CamelSnakeConverter,
    aname_transform=SnakeCamelConverter,
    ftype=Attribute
)
```

### 2. XML Namespaces

Support for XML namespaces:

Use the XmlNamespaces class to define the namespaces for XML serialization. This object
can be passed to the XmlSerializationSpec class to define the namespaces for serialization.

```python
NAMESPACES = XmlNamespaces(
    xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02",
    xml="http://www.w3.org/XML/1998/namespace"
)

@xdatatree
class Component:
    XDATATREE_CONFIG = DEFAULT_CONFIG(xmlns=NAMESPACES.xmlns)
    path: str = xfield(xmlns=NAMESPACES.p, doc='Path')
    id: str = xfield(xmlns=None, doc='ID')

...

# Create the serialization specification with the namespaces specified.
SERIALIZATION_SPEC = XmlSerializationSpec(
    Root, # Your root class
    'root', # Root element name
    namespaces=NAMESPACES,
    options=XmlParserOptions(assert_unused_elements=True, assert_unused_attributes=True)
)

# Deserialize from XML
xml_tree = etree.fromstring(xml_string)
model, status = SERIALIZATION_SPEC.deserialize(xml_tree)

#Serialize to XML
xml_element = SERIALIZATION_SPEC.serialize(model)
```

### 3. Custom Value Collectors

For special collection handling:

```python
@datatree
class CustomCollector(ValueCollector):
    values: List[Any] = dtfield(default_factory=list)
    CONTAINED_TYPE = YourXdatatreeClass
    def append(self, item: CONTAINED_TYPE):
        self.values.append(item)
    def get(self):
        return self.values
    @classmethod
    def to_contained_type(cls, value):
        return value
```

#### Triangle Custom Value Collector Example

In this example we create a custom value collector for a field representing a list of triangles.
The Triangle class is defined as an xdatatree class and the TriangesCustomConverter is a custom value collector that will collect the triangles and paint colors and serialize them back to a list of XML triangles.

```python
@xdatatree
class Triangle:
    # An xml representation of a triangle: <triangle v1="1" v2="2" v3="3" paint_color="red"/>
    v1: int = xfield(ftype=Attribute, doc='V1 of the triangle')
    v2: int = xfield(ftype=Attribute, doc='V2 of the triangle')
    v3: int = xfield(ftype=Attribute, doc='V3 of the triangle')
    paint_color: str = xfield(ftype=Attribute, doc='paint_colors of the triangle')
    
    def get_array(self):
        return np.array([self.v1, self.v2, self.v3])

@datatree
class TriangesCustomConverter(ValueCollector):
    '''A custom converter for a field representing a list of Triange objects.
    This will represent the list of trianges as a numpy array and allow to serialize it
    back to a list of Triange objects.'''
    triangles: List[np.ndarray] = dtfield(default_factory=list, doc='List of vertices')
    paint_colors: List[str] = dtfield(default_factory=list, doc='List of paint colors')
    
    # This is used to read and write the values as xml element.
    CONTAINED_TYPE = Triangle
    
    def append(self, item: CONTAINED_TYPE):
        if not isinstance(item, self.CONTAINED_TYPE):
            raise ValueError(f'Item must be of type {self.CONTAINED_TYPE.__name__} but received {type(item).__name__}')
        self.triangles.append(item.get_array())
        self.paint_colors.append(item.paint_color)

    def get(self):
        return np.array(self.triangles), self.paint_colors
    
    @classmethod
    def to_contained_type(cls, triangles_paint_colors: Tuple[np.ndarray, List[str]]):
        return (cls.CONTAINED_TYPE(*x[0], paint_color=x[1]) for x in zip(*triangles_paint_colors))
```


### 4. Parser Options

Control parsing behavior:

```python
from anchorscad.xdatatrees import XmlParserOptions
options = XmlParserOptions(
    assert_unused_elements=True,
    assert_unused_attributes=True,
    print_unused_elements=True
)
```


## Best Practices

1. Define a `XDATATREE_CONFIG` for the most common field configuration.
2. Use descriptive documentation in `xfield(doc='...')`
3. Use custom converters and ValueCollectors to make the resulting data structure require no further processing.
4. Use the XmlNamespaces class and pass it to the XmlSerializationSpec.


## Error Handling

The module provides several error types:

- `TooManyValuesError`: When multiple values are provided for a single-value field
- `ConversionException`: When value conversion fails
- `MatrixShapeError`: When matrix dimensions are incorrect

Elements and attributes fields are not defined can be either treated as errors or collected in as `unknown_elements` and `unknown_attributes` lists where they can be handled in an application specific way.

```python
# Deserialize with error checking
model, status = SERIALIZATION_SPEC.deserialize(xml_tree)

# Check for parsing issues
if status.contains_unknown_elements:
    print("Warning: Found unknown XML elements")
if status.contains_unknown_attributes:
    print("Warning: Found unknown XML attributes")

# get an xdatatree object to report on missing elements and attributes. This may
# require walking the tree to find the node that contains the missing elements and attributes.

if node.contains_unknown_elements:
    print(f'XML node {node.__class__.__name__} contains unknown elements:')
    print(node.xdatatree_unused_xml_elements)
if node.contains_unknown_attributes:
    print(f'XML node {node.__class__.__name__} contains unknown attributes:')
    print(node.xdatatree_unused_xml_attributes)

Alternatively, the `XmlParserOptions` can be set to print the unused elements and attributes.

```python
SERIALIZATION_SPEC = XmlSerializationSpec(
    Model, # Your root class
    'model', # Root element name
    namespaces=NAMESPACES,
    options=XmlParserOptions(print_unused_elements=True, print_unused_attributes=True)
)
```

## Installation

```bash
pip install xdatatrees
```

## Limitations

Dataclasses InitVar annotations are not supported. Reasonable proposals are welcome.

## License

This package is licensed under LGPLv2.1 - see the LICENSE file for details.

## Acknowledgments

This was inspired by anchorscad's need to serialize and deserialize 3mf files. The use
of datatrees which also came out of anchorscad's need for a more feature rich dataclasses
decorator was primarily for the documentation datatree feature but also the full set of
datatrees features are available to the xdatatree decorator and xfield specifier.
