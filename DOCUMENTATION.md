# **xdatatrees – Declarative XML Serialization for Dataclasses**

**`xdatatrees`** is a Python library built on top of the [**`datatrees`**](https://github.com/owebeeone/datatrees) framework (which itself extends Python's **`dataclasses`**) to provide a clean, declarative API for mapping between XML documents and Python objects. It eliminates much of the boilerplate code typically required for XML serialization and deserialization while maintaining type safety and comprehensive error handling. In essence, xdatatrees allows you to define how XML should map to Python classes using simple class definitions and annotations, and it takes care of the rest.

## **Installation**

Install xdatatrees from PyPI using pip:

```sh
pip install xdatatrees
```

This will also install the core **datatrees** library as a dependency, since xdatatrees builds on it.

## **Core Features**

Key features of xdatatrees include:

* **Declarative XML Mapping:** Map Python classes to XML using simple annotations (class definitions act as the schema).

* **Automatic Type Conversion:** Built-in conversion between Python types (e.g. int, float, bool) and their XML string representations.

* **Flexible Field Types:** Support for mapping class fields to XML attributes, nested elements, text content, and metadata elements.

* **Namespace Support:** Full XML namespace handling with automatic prefix management for complex XML documents.

* **Custom Converters:** Extensible system for handling complex data types via custom converter classes (for example, converting a matrix or special data structure to/from string).

* **Value Collectors:** Specialized handling for collections and aggregated data, allowing custom accumulation or transformation of repeated XML elements into optimized Python representations.

* **Comprehensive Error Handling:** Detailed error reporting, including detection of unused (unexpected) XML elements/attributes during parsing.

* **Name Transformations:** Automatic conversion between naming conventions (e.g. `CamelCase` XML names to `snake_case` Python names, and vice versa).

## **Why xdatatrees?**

### **The Challenge of XML Processing**

Working with XML in Python often involves verbose, error-prone manual coding. For example, using the standard library you might parse and construct XML like this:

```python
# Without xdatatrees – manual XML processing  
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

While this works, it has several problems:

* **Manual type conversion and validation:** e.g. converting the age to int and back to string by hand.

* **No clear schema mapping:** The relationship between the XML structure and the Python data (dictionary in this case) is implicit and not enforced.

* **Error-prone handling:** It’s easy to miss or mis-handle attributes and elements (e.g. forgetting to check if an element exists).

* **No namespace support:** Adding XML namespaces would complicate the code further.

* **Hard to maintain:** Changes in the XML schema require manual changes in multiple places in the code, increasing the chance of errors.

### **xdatatrees: Declarative XML Processing**

**Xdatatrees** addresses these issues by allowing you to define a Python class that directly mirrors the XML structure. You decorate classes with `@xdatatree` and declare fields using `xfield` with field types to indicate how they map to XML. For example, using xdatatrees you can rewrite the above example declaratively:

# With xdatatrees – declarative and type-safe  
from xdatatrees import xdatatree, xfield, Attribute, TextElement

```python
@xdatatree  
class Person:  
    name: str = xfield(ftype=Attribute, doc='Person name')  
    age: int = xfield(ftype=Attribute, doc='Person age')  
    address: str = xfield(ftype=TextElement, doc='Person address')

# Now Person corresponds to an XML <person> element with 'name' and 'age' as attributes,  
# and an <address> child element containing text.  
# Automatic serialization/deserialization will be handled by xdatatrees (see usage below).
```

In this `Person` class definition, we specify that `name` and `age` should be stored as XML attributes (using the `Attribute` field type) and `address` as a text-containing subelement (using `TextElement`). The `doc` strings are optional but provide documentation. With this setup, xdatatrees can automatically create or parse XML for `Person` objects with full type safety and minimal code.

#### **Benefits**

Using xdatatrees provides several benefits:

1. **Type Safety:** Fields are automatically converted to the correct types (with validation). For instance, `age` will always be parsed as an integer, or an error is raised if the XML has a non-integer value.

2. **Clear Schema Definition:** The class structure itself documents the expected XML schema (the class is essentially a schema for the XML). This makes the code self-documenting and easier to understand.

3. **Maintainability:** Changes to the XML format (like adding or renaming fields) typically only require updating the class definition in one place, rather than scattered procedural code.

4. **Namespace Awareness:** xdatatrees has built-in support for XML namespaces, so working with XML that uses multiple namespaces is straightforward (you can define namespace mappings once and use them for relevant fields).

5. **Robust Error Handling:** The library can warn you about unexpected XML content (unknown elements or attributes) and provides clear exceptions for common issues (such as providing too many values for a field that expects only one) – making it easier to catch mistakes early.

6. **Extensibility:** You can define custom field converters for complex types and custom value collectors for aggregating data, allowing xdatatrees to handle advanced use cases like geometry, scientific data, etc., without losing the benefits of automation.

## **Basic Usage**

This section covers basic usage patterns for xdatatrees, from simple mappings to collections and performing serialization/deserialization.

### **1. Simple XML Mapping**

For a basic example, consider modeling a single person as in the earlier example. We can define a `Person` class with xdatatrees as follows:

```python
from xdatatrees import xdatatree, xfield, Attribute, TextElement  
from typing import List

# Define a default field configuration (optional, for brevity)  
DEFAULT_CONFIG = xfield(ftype=Attribute)  # default: treat fields as XML attributes

@xdatatree  
class Person:  
    XDATATREE_CONFIG = DEFAULT_CONFIG  # Apply default to all fields unless overridden  
    name: str = xfield(doc='Person name')  
    age: int = xfield(doc='Person age')   
    address: str = xfield(ftype=TextElement, doc='Person address')  # override default for this field
```

In this `Person` class:

* We set a class variable `XDATATREE_CONFIG = DEFAULT_CONFIG` to specify that, by default, all fields should be treated as XML attributes (using `Attribute`) unless specified otherwise. This saves repetition for classes where most fields are attributes.

* We then declare `name` and `age` with no explicit `ftype`, so they inherit the default and become XML attributes.

* The `address` field we override to use `TextElement` as its field type, meaning it will appear as a child element (with text content) instead of an XML attribute.

With this definition, a `Person(name="John", age=30, address="123 Main St")` will correspond to the XML:

```xml
<person name="John" age="30">  
  <address>123 Main St</address>  
</person>
```

This shows how the class definition directly maps to XML structure: the class name `Person` is not automatically used in XML (we'll specify the root element name during serialization), but the fields and their types determine the XML content.

### **2. Working with Lists and Collections**

xdatatrees supports nested datatree classes and collections. Suppose we want an XML that contains multiple `<person>` entries, e.g.:

```xml
<people count="2">  
  <person name="John" age="30"><address>123 Main St</address></person>  
  <person name="Jane" age="25"><address>456 Oak Ave</address></person>  
</people>
```

We can represent this with a `People` class containing a list of `Person` objects:

```python
from xdatatrees import xdatatree, xfield, Attribute, Element

@xdatatree  
class People:  
    XDATATREE_CONFIG = xfield(ftype=Element)  # default: treat fields as child elements  
    people: List[Person] = xfield(doc='List of people')  
    count: int = xfield(ftype=Attribute, doc='Total count')
```

Here, we set the default field type to `Element` for this class, because by default we expect fields to be sub-elements (this is appropriate since `People.people` will be a collection of sub-elements). In the `People` class:

* The field `people: List[Person]` is a list of `Person` objects, and by default (due to `XDATATREE_CONFIG`) each `Person` in the list will be serialized as a `<person>` child element. The field name `people` by default would determine the tag name of each child, but as it’s a list of a datatree class, xdatatrees will actually use the class name or another strategy (see **Name Transformations** below). In practice, as shown above, each item appears as `<person>` in XML, matching the `Person` class name in lowercase.

* The field `count: int` we explicitly mark as an `Attribute`, representing a count of persons. This will appear as an attribute on the `<people>` root element.

When a `People` instance is serialized, `xdatatrees` maps the `count` field to an XML attribute and generates a child element for each `Person` object in the list. For example, serializing a `people_obj` containing two `Person` entries (John and Jane) would produce XML similar to the snippet above. Deserializing that XML, in turn, reconstructs the `People` object, populating the list with two `Person` objects and setting the `count` field from the corresponding XML attribute.

### **3. Serialization and Deserialization**

To convert between your Python classes and XML, xdatatrees uses a serialization specification object. This specification ties a top-level class to an XML root element name (and optionally XML namespaces and parsing options).

First, create an `XmlSerializationSpec` for the root class. For example, continuing the people example:

from xdatatrees import XmlSerializationSpec  
import xml.etree.ElementTree as ET

# Create serialization specification for the root element  
SERIALIZATION_SPEC = XmlSerializationSpec(  
    People,        # The root datatree class  
    'people',      # The XML root element name to map to this class  
    xml_namespaces=None  # Optional: namespace mappings if any (None for now)  
)

Here, we tell xdatatrees that the `People` class corresponds to an XML document rooted at a `<people>` element. If we had any XML namespaces to use, we could supply an `XmlNamespaces` object (discussed later) via the `xml_namespaces` parameter.

Now we can **deserialize** XML into Python objects:

```python
# Example XML input  
xml_string = '''  
<people count="1">  
    <person name="Alice" age="28">  
        <address>789 Pine Rd</address>  
    </person>  
</people>  
'''  
xml_tree = ET.fromstring(xml_string)

# Deserialize XML into a People object  
people_obj, status = SERIALIZATION_SPEC.deserialize(xml_tree)  
print(f"Count: {people_obj.count}")                 # Count: 1  
print(f"First person: {people_obj.people[0].name}")  # First person: Alice
```

Using `deserialize`, we get back a tuple `(obj, status)`: `obj` is an instance of `People` populated from the XML, and `status` is an object containing information about the parsing (such as whether any unknown elements/attributes were encountered, etc.). Here we see the `count` field was read as `1` and the first person’s name is "Alice", as expected from the XML.

Likewise, we can **serialize** a Python object back to XML:

```python
# Serialize the People object back to XML  
xml_element = SERIALIZATION_SPEC.serialize(people_obj)  
xml_string_out = ET.tostring(xml_element, encoding='unicode')  
print(xml_string_out)
```

The `serialize` method returns an `xml.etree.ElementTree.Element` (root XML element) which we can convert to a string for output or further processing. In this case, `xml_string_out` should be equivalent to the original `xml_string` (modulo minor differences like whitespace or attribute ordering).

Together, `XmlSerializationSpec.deserialize` and `XmlSerializationSpec.serialize` provide a round-trip conversion between XML and your datatree-defined Python objects.

## **Field Types**

xdatatrees supports four main types of field mappings, controlled by the `ftype` argument to `xfield`. These determine how a given class field is represented in XML:

### **Attribute Fields**

Using `ftype=Attribute` on an `xfield` maps that field to an **XML attribute** on the element for that class. For example:

from xdatatrees import xdatatree, xfield, Attribute

```python
@xdatatree  
class Product:  
    id: str = xfield(ftype=Attribute)  
    price: float = xfield(ftype=Attribute)
```

Instances of `Product` will be represented as `<product>` XML elements with `id` and `price` as attributes:

```xml
<product id="ABC123" price="29.99" />
```

In code, `Product(id="ABC123", price=29.99)` would serialize to the above XML, and deserializing that XML would yield a `Product` object with `id="ABC123"` (string) and `price=29.99` (float). You get automatic type conversion for the price attribute from string to float.

### **Element Fields**

Using `ftype=Element` on an `xfield` indicates the field is a **nested element** containing either another datatree class or a collection of them. This is used to model hierarchical data.

For example, if a `Person` has an `Address` as a sub-element:

```python
from xdatatrees import xdatatree, xfield, Attribute, Element

@xdatatree  
class Address:  
    street: str = xfield(ftype=Attribute)  
    city: str = xfield(ftype=Attribute)

@xdatatree  
class Person:  
    name: str = xfield(ftype=Attribute)  
    address: Address = xfield(ftype=Element)
```

Here, `Person.address` is a field of type `Address` and marked as an Element, so it will appear as an `<address>` child element inside `<person>`. The `Address` class itself defines its fields as attributes (street and city). The XML for `Person(name="John", address=Address(street="123 Main St", city="Anytown"))` would look like:

```xml
<person name="John">  
  <address street="123 Main St" city="Anytown" />  
</person>
```

Element fields are also how you include **lists** of datatrees (as shown in the `People` example earlier): a list of datatree objects is treated as multiple child elements.

### **TextContent Feilds**

Using `ftype=TextContext` maps a field to the current element's **text content** (rather than nested child elements or attributes). This is useful for simple data values that should appear as text in the XML.


```python
from xdatatrees import xdatatree, xfield, Attribute, Element

@xdatatree  
class Address:  
    label: str = xfield('work', ftype=Attribute, doc='address label')
    address: str = xfield(ftype=TextContent)

@xdatatree  
class Person:  
    name: str = xfield(ftype=Attribute)  
    address: Address = xfield(ftype=Element)
```


### **TextElement Fields**

Using `ftype=TextElement` maps a field to an XML element that contains **text content** (rather than nested child elements or attributes). This is useful for simple data values that should appear as text in the XML.

For example:

```python
from xdatatrees import xdatatree, xfield, TextElement

@xdatatree  
class Product:  
    name: str = xfield(ftype=TextElement)  
    price: float = xfield(ftype=TextElement)  
    in_stock: bool = xfield(ftype=TextElement)
```

Here, each field will become a child element of `<product>` with the field name as the tag and the field value as the text content. A `Product(name="Widget", price=29.99, in_stock=True)` would serialize to:

```xml
<product>  
  <name>Widget</name>  
  <price>29.99</price>  
  <in_stock>true</in_stock>  
</product>
```

Notice that booleans like `True`/`False` are automatically converted to `"true"`/`"false"` strings in XML, and back to Python bool on parsing.

### **Metadata Fields**

Using `ftype=Metadata` is a special case intended for key-value metadata representation in XML. In many XML schemas, you have a generic way to attach key-value pairs, often with tags like `<metadata key="...">`. xdatatrees handles this pattern with the `Metadata` field type.

For example:

```python
from xdatatrees import xdatatree, xfield, Metadata

@xdatatree  
class Product:  
    category: str = xfield(ftype=Metadata)
```

This would map the `category` field to a metadata entry in XML, e.g.:

```xml
<product>  
  <metadata key="category" value="electronics" />  
</product>
```

Here, the field name (`category`) becomes the `key` attribute and the field value (`"electronics"`) becomes the `value` attribute in a `<metadata>` element. On deserialization, xdatatrees will find the `<metadata key="category" ...>` element and set the `category` field accordingly. This mechanism is helpful for schemas that allow arbitrary metadata fields.

## **Advanced Features**

Beyond basic mappings, xdatatrees offers advanced capabilities for handling more complex scenarios.

### **1. Custom Converters for Complex Types**

Sometimes your data might not be a simple int/float/bool/string. For example, you might want to include a matrix or a date, or other structured data that needs a custom conversion to and from a string form in XML. xdatatrees allows you to define **custom converter classes** for such fields.

A custom converter is essentially a small datatree (or dataclass) that encapsulates how to parse and stringify a complex object. You typically mark such a converter class with the `@datatree` decorator (from the core datatrees library) and define how it converts in its `__init__` and `__str__` methods.

For example, suppose we want to include a 4x4 transformation matrix in our XML as a space-separated string. We can define a converter like:

```python
from xdatatrees import xdatatree, xfield, Attribute, Metadata  
from datatrees import datatree, dtfield  # using core datatrees for converter  
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
            # Parse input string like "1 0 0 0  0 1 0 0  0 0 1 0  0 0 0 1"  
            values = [float(x) for x in re.split(r's+', matrix_input.strip())]  
            if len(values) != 16:  
                raise ValueError(f"Expected 16 values, got {len(values)}")  
            self.matrix = np.array(values).reshape((4, 4))

    def __str__(self):  
        # Convert the matrix back to a space-separated string  
        return ' '.join(str(x) for x in self.matrix.flatten())
```

This `MatrixConverter` class can take either a NumPy array or a string in its constructor and will produce a normalized 4x4 NumPy array. The `__str__` method outputs the space-separated string form. Now we can use this in an xdatatrees class:

```python
@xdatatree  
class Transform:  
    XDATATREE_CONFIG = xfield(ftype=Metadata)  # default all fields to Metadata entries  
    id: str = xfield(ftype=Attribute, doc='Transform ID')  
    matrix: MatrixConverter = xfield(doc='Transformation matrix')
```

By setting `XDATATREE_CONFIG` to use `Metadata`, we ensure that by default fields (like `matrix`) will be stored as `<metadata>` entries. The `id` field we override to be an XML attribute.

Now a `Transform` object might serialize to:

```xml
<transform id="T1">  
  <metadata key="matrix" value="1 0 0 5  0 1 0 10  0 0 1 0  0 0 0 1"/>  
</transform>
```

In this XML, the matrix is stored as a single string in the `value` attribute of a `<metadata>` element with key "matrix". When deserializing, xdatatrees will instantiate `MatrixConverter` with that string, and our `MatrixConverter` will parse it into a NumPy array. Thus, `transform_obj.matrix` ends up as a `MatrixConverter` containing the `np.ndarray`, which we can then use in Python (and we defined `__str__` such that serializing back is seamless).

Custom converters are a powerful way to extend xdatatrees for complex data without losing the declarative approach.

### **2. XML Namespaces**

XML Namespaces allow elements and attributes to be differentiated by a URI (commonly using prefixes). xdatatrees provides full namespace support. You can define namespaces and associate them with fields or classes using the `XmlNamespaces` helper and the `xmlns` parameter in `xfield`.

First, define your namespaces:

from xdatatrees import XmlNamespaces

# Define XML namespaces with optional prefixes  
NAMESPACES = XmlNamespaces(  
    xmlns="http://schemas.example.com/model/2023",    # default namespace (no prefix)  
    geom="http://schemas.example.com/geometry/2023",  # namespace with prefix 'geom'  
    mat="http://schemas.example.com/materials/2023"   # namespace with prefix 'mat'  
)

Here, we defined three namespaces: a default namespace (referred as `xmlns`), and two others with prefixes `geom` and `mat`. The keys in `XmlNamespaces(...)` become attributes of `NAMESPACES` for convenience, e.g. `NAMESPACES.geom` holds the namespace URI for the geometry namespace.

Now, use these in a datatree class. For example:

```python
@xdatatree  
class Component:  
    # Apply a default namespace to all attributes by default  
    XDATATREE_CONFIG = xfield(xmlns=NAMESPACES.xmlns, ftype=Attribute)

    id: str = xfield(doc='Component ID')  
    geometry_ref: str = xfield(xmlns=NAMESPACES.geom, doc='Geometry reference')  
    material_id: str = xfield(xmlns=NAMESPACES.mat, doc='Material ID')
```

In this `Component` class:

* We set `XDATATREE_CONFIG` such that, unless otherwise specified, fields will be treated as attributes in the default namespace (`xmlns`). That means `id` by default uses the default namespace (since we didn’t override its `xmlns` in its own xfield call).

* For `geometry_ref`, we specify `xmlns=NAMESPACES.geom`, meaning this field will be an attribute in the `geom` namespace. Similarly, `material_id` will be an attribute in the `mat` namespace.

Next, when creating the `XmlSerializationSpec` for this class, we provide the `xml_namespaces`:

```python
SERIALIZATION_SPEC = XmlSerializationSpec(  
    Component,  
    'component',        # root element name  
    xml_namespaces=NAMESPACES  
)
```

When serializing a `Component` object, xdatatrees will include the namespace declarations on the root element and apply the namespaces to the specified fields. For example:

```xml
<component xmlns="http://schemas.example.com/model/2023"  
           xmlns:geom="http://schemas.example.com/geometry/2023"  
           xmlns:mat="http://schemas.example.com/materials/2023"  
           id="C001"   
           geom:geometry_ref="G001"  
           mat:material_id="M001" />
```

Here, `id` is in the default namespace (no prefix), `geometry_ref` is in the `geom` namespace, and `material_id` is in the `mat` namespace. The `XmlNamespaces` provided to `XmlSerializationSpec` ensures the appropriate `xmlns` declarations (`xmlns`, `xmlns:geom`, `xmlns:mat`) appear on the root element.

On deserialization, the presence of those namespaces and prefixes will be handled automatically by xdatatrees, and it will map the attributes back to the correct fields.

### **3. Name Transformations**

Sometimes XML uses a different naming convention (e.g. camelCase) than your Python code (which might use snake_case). xdatatrees can handle automatic name transformations for both element names and attribute names using converter classes like `CamelSnakeConverter` and `SnakeCamelConverter`.

For example, suppose your XML uses camelCase for everything, but you want to use snake_case in Python. You can set up a class like:

```python
from xdatatrees import xdatatree, xfield, Attribute, TextElement, CamelSnakeConverter, SnakeCamelConverter

@xdatatree
class APIResponse:
    XDATATREE_CONFIG = xfield(
        ename_transform=CamelSnakeConverter,   # transform element names: CamelCase -> snake_case
        aname_transform=SnakeCamelConverter,   # transform attribute names: snake_case -> CamelCase
        ftype=Attribute                        # default to attributes for fields
    )
    user_id: str = xfield(doc='User identifier')       # will become 'UserId' attribute in XML
    creation_date: str = xfield(ftype=TextElement, doc='Creation date')  # will remain 'creation_date' element
    ModificationDate: str = xfield(ftype=TextElement, doc='Modification date')  # will become 'modification_date'
```

In `XDATATREE_CONFIG`, we provided:

*   `ename_transform=CamelSnakeConverter`: this means that for element names, xdatatrees will convert from `CamelCase` to `snake_case`.
*   `aname_transform=SnakeCamelConverter`: for attribute names, xdatatrees will convert from `snake_case` to `CamelCase`.

Given this configuration:

*   The `user_id` field, being an `Attribute`, will be transformed by `aname_transform` from `user_id` to `UserId`.
*   The `creation_date` field is a `TextElement`, so it is transformed by `ename_transform`. Since it is already in `snake_case`, it remains as `creation_date`.
*   The `ModificationDate` field is also a `TextElement`, so it is transformed by `ename_transform` from `CamelCase` to `modification_date`.

This feature is particularly useful if you need to interface with XML that has a certain naming style without having to litter your code with unnatural naming. xdatatrees can keep your Python code Pythonic and still meet the XML spec.

### **4. Handling Repeated Elements**

A common pattern in XML is a collection of repeated elements, such as a list of items. `xdatatrees` handles this by mapping a Python `List` of `xdatatree` objects to a corresponding series of XML elements.

For instance, imagine an XML that contains many `<triangle>` elements. You can model this in `xdatatrees` with a `Mesh` class that contains a list of `Triangle` objects.

```python
from xdatatrees import xdatatree, xfield, Attribute, Element
from typing import List

@xdatatree
class Triangle:
    v1: int = xfield(ftype=Attribute)
    v2: int = xfield(ftype=Attribute)
    v3: int = xfield(ftype=Attribute)
    color: str = xfield(ftype=Attribute)

@xdatatree
class Mesh:
    triangles: List[Triangle] = xfield(ftype=Element)
```

In this example, the `Mesh` class has a `triangles` field which is a `List[Triangle]`. The `ftype=Element` on this field tells `xdatatrees` that each item in the list should be serialized as a child element. By default, `xdatatrees` will use the field name (`triangles`) as the tag name for each element in the list.

When serializing a `Mesh` instance, `xdatatrees` will iterate over the `triangles` list and create a `<triangles>` element for each `Triangle` object. When deserializing, it will collect all `<triangles>` child elements of `<mesh>`, convert each one into a `Triangle` object, and populate the `triangles` list.

This approach allows you to work with collections of structured data in a natural, Pythonic way, while `xdatatrees` handles the conversion to and from the XML representation.

## **Error Handling and Validation**

xdatatrees provides comprehensive error handling features to help you validate XML input against your datatree schema and handle unexpected content gracefully.

### **1. Parser Options**

When setting up your `XmlSerializationSpec`, you can provide an `XmlParserOptions` object to control how strict the parsing should be and what to do with unrecognized content.

```python
from xdatatrees import XmlParserOptions, XmlSerializationSpec

# Strict parsing – fail on unknown elements/attributes  
strict_options = XmlParserOptions(  
    assert_unused_elements=True,     # raise error if unknown elements are encountered  
    assert_unused_attributes=True,   # raise error if unknown attributes are encountered  
    print_unused_elements=True       # optionally print warnings for debugging  
)

SERIALIZATION_SPEC = XmlSerializationSpec(  
    MyClass,  
    'root',  
    options=strict_options  
)
```

With these options set:

* If during deserialization an XML element is found that doesn’t correspond to any field in your datatree classes, an error will be raised (because `assert_unused_elements=True`).

* Similarly for unknown attributes.

* The `print_unused_elements=True` can be useful during development to log warnings about unused content instead of immediately erroring, so you can debug or update your classes.

If you prefer a more lenient parse (e.g., ignore unknown tags), you can set those flags to False. By default, if not provided, xdatatrees might simply ignore unknown elements/attributes but still record them in the status (see next section).

### **2. Handling Unknown XML Content**

Even without strict mode, you might want to know if the XML had extra content that was not mapped to your classes. The `status` object returned by `deserialize` helps with this.

Example usage:
```python
model, status = SERIALIZATION_SPEC.deserialize(xml_tree)

# Check for parsing issues  
if status.contains_unknown_elements:  
    print("Warning: Found unknown XML elements")  
    # You can examine which elements were unknown:  
    # e.g., status might aggregate info, or you can inspect the resulting object

if status.contains_unknown_attributes:  
    print("Warning: Found unknown XML attributes")
```

The `status.contains_unknown_elements` and `.contains_unknown_attributes` flags indicate if anything in the XML didn’t match your datatree definitions.

xdatatrees also populates each object in the hierarchy with details about unknown content, if any, using special attributes. For example, any datatree object may have:

* `obj.xdatatree_unused_xml_elements` – a list of unknown XML sub-elements found under that object’s element.

* `obj.xdatatree_unused_xml_attributes` – a dict or list of unknown XML attributes on that object’s element.

And correspondingly boolean flags `obj.contains_unknown_elements` or `obj.contains_unknown_attributes`. You can traverse your object tree to find where the unknown content was. For instance:

```python
def check_unknown_content(node):  
    if hasattr(node, 'contains_unknown_elements') and node.contains_unknown_elements:  
        print(f'Node {node.__class__.__name__} has unknown elements:')  
        print(node.xdatatree_unused_xml_elements)  
    if hasattr(node, 'contains_unknown_attributes') and node.contains_unknown_attributes:  
        print(f'Node {node.__class__.__name__} has unknown attributes:')  
        print(node.xdatatree_unused_xml_attributes)
```

You might call `check_unknown_content` on your root object and its children to identify any unmapped XML content. This is especially useful if you receive evolving XML and want to ensure your classes stay in sync with the XML schema, or to issue warnings when extra data is present.

### **3. Common Error Types**

xdatatrees defines specific exception types for certain error conditions, which you can catch and handle. For example, if an XML provides multiple values for a field that was expected to hold a single value, a `TooManyValuesError` may be raised.

Usage example:

```python
from xdatatrees import TooManyValuesError

try:  
    model, status = SERIALIZATION_SPEC.deserialize(xml_tree)  
except TooManyValuesError as e:  
    print(f"Multiple values provided for single-value field: {e}")  
except Exception as e:  
    print(f"General parsing error: {e}")
```

In this snippet, if the XML had, say, two `<name>` elements but your class expects only one (i.e. a single field, not a list), xdatatrees could raise `TooManyValuesError`. By catching it, you can handle that scenario separately from other exceptions. Other exceptions might include type conversion errors (ValueError, etc.), which you can catch generally or specifically if needed.

Using these error handling tools, you can make your XML parsing robust: strict when you want it to be, or flexible but with the ability to log or handle any irregularities.

## **Best Practices**

When using xdatatrees, consider the following best practices to make your code clearer and more robust:

1. **Use `XDATATREE_CONFIG` for Defaults:** Defining a class-level `XDATATREE_CONFIG` (as shown in earlier examples) is very useful. For example, set common defaults like `DEFAULT_CONFIG = xfield(ftype=Attribute, ename_transform=CamelSnakeConverter)` and then assign `XDATATREE_CONFIG = DEFAULT_CONFIG` in your classes to apply those defaults. This reduces repetition and ensures consistency across fields.

**Document Your Fields:** Use the `doc` parameter in `xfield` to provide a description for each field. This documentation is preserved through the datatree chain and is accessible via utilities (like `field_docs` in datatrees). It greatly helps readability and maintenance. For instance:

```python
 name: str = xfield(doc='User full name (first and last)')
```

2.  provides context for what that field represents.

3. **Leverage Custom Converters:** Don’t hesitate to create small converter classes (as shown with `MatrixConverter`) for any complex logic. This keeps your main class definitions simple and offloads parsing/formatting logic to dedicated classes which can be tested separately.

4. **Use Namespaces in Specs:** If you know your XML will use namespaces, define an `XmlNamespaces` object and always pass it to `XmlSerializationSpec`. This ensures that namespace declarations are handled automatically and consistently. In production XML, namespace usage is common, so handling them explicitly is important.

5. **Handle Errors Gracefully:** Decide on your parsing strategy early – whether to be strict or lenient – and use `XmlParserOptions` accordingly. In lenient mode, make use of the `status` and unknown content tracking to inform you of any discrepancies. This way, your application can log warnings or adapt without failing unpredictably.

6. **Mind Your Type Annotations:** xdatatrees relies on Python type annotations to do conversions. Make sure your field types are accurate (e.g., if a field is optional, consider using `Optional[int]` or provide a default of `None` if that’s allowed in your XML). If the type is wrong, the conversion will either error or produce incorrect data.

7. **Validate Early:** During development or testing, use strict parser options (`assert_unused_elements/attributes=True`) to catch mismatches between your classes and the XML schema. This will surface issues early so you can adjust your model classes or handle new XML content accordingly.

By following these practices, you can make the most of xdatatrees and ensure your XML handling code is clean, reliable, and easy to maintain.

## **Complete Example: 3D Model Serialization**

To illustrate xdatatrees in a more complex scenario, consider a 3D model file format (for example, a 3MF file) that contains information about materials, geometry (vertices, triangles), etc. xdatatrees can be used to define classes that map to such an XML structure. Below is a simplified but comprehensive example of using many of the features together:

```python
from xdatatrees import xdatatree, xfield, Attribute, Element, Metadata  
from xdatatrees import XmlSerializationSpec, XmlNamespaces, XmlParserOptions  
from datatrees import datatree, dtfield  
from typing import List  
import xml.etree.ElementTree as ET

# Define XML namespaces to be used  
NAMESPACES = XmlNamespaces(  
    xmlns="http://schemas.example.com/3d/2023",        # default namespace for model  
    material="http://schemas.example.com/materials/2023"  # separate namespace for materials  
)

# Field default: by default use attributes in the default namespace for fields  
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

@xdatatree  
class Mesh:  
    XDATATREE_CONFIG = xfield(xmlns=NAMESPACES.xmlns, ftype=Element)  
    material_id: str = xfield(ftype=Attribute, doc='Associated material')  
    vertices: List[Vertex] = xfield(doc='Mesh vertices')  
    triangles: List[Triangle] = xfield(doc='Mesh triangles')

@xdatatree  
class Model:  
    XDATATREE_CONFIG = xfield(xmlns=NAMESPACES.xmlns, ftype=Element)  
    name: str = xfield(ftype=Attribute, doc='Model name')  
    materials: List[Material] = xfield(doc='Available materials')  
    meshes: List[Mesh] = xfield(doc='Model meshes')

# Create a serialization spec for Model  
SPEC = XmlSerializationSpec(  
    Model,  
    'model',  
    xml_namespaces=NAMESPACES,  
    options=XmlParserOptions(assert_unused_elements=True)  # strict mode for unknown elements  
)

# Create an example Model instance
model = Model(
    name="Simple Cube",
    materials=[
        Material(id="mat1", name="Red Plastic")
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

# Serialize the model to XML  
xml_element = SPEC.serialize(model)  
xml_string = ET.tostring(xml_element, encoding='unicode')  
print("Generated XML:")  
print(xml_string)

# Now deserialize the XML back to a Model object  
xml_tree = ET.fromstring(xml_string)  
restored_model, status = SPEC.deserialize(xml_tree)

print(f"nRestored model name: {restored_model.name}")  
print(f"Material count: {len(restored_model.materials)}")  
print(f"Vertex count (in first mesh): {len(restored_model.meshes[0].vertices)}")
```

This example brings together multiple pieces:

* Multiple classes with their own `XDATATREE_CONFIG` defaults (mixing attributes and elements, and a second namespace for `Material`).

* A `Model` class that ties everything together (one model contains materials and meshes).

* Use of `XmlNamespaces` to handle the default namespace and a prefixed namespace.

* Use of `XmlParserOptions` to enforce no unknown elements.

* Creation of an object, serialization to XML, and deserialization back to an object to verify the round-trip.

When you run this, you would see the generated XML (which would include namespace declarations and all data), and the printed details of the restored model confirming that everything was parsed correctly. This demonstrates how xdatatrees can be used for complex structured data without a lot of imperative XML parsing code.

## **Limitations**

While xdatatrees is powerful, it has some current limitations to be aware of:

* **InitVar Support:** If you use `dataclasses.InitVar` in your classes (a feature of dataclasses for initialization-only variables), xdatatrees does not currently support these. All fields in xdatatrees classes should be normal fields (or `InitVar` will be ignored).

* **Circular References:** xdatatrees (and datatrees/dataclasses in general) don’t handle circular references between objects. If two objects reference each other, serialization/deserialization would be problematic. You may need to break such cycles or handle those relations outside of xdatatrees.

* **Schema Validation:** xdatatrees focuses on converting between XML and objects, but it does not perform XML Schema (XSD) validation. It will ensure the structure matches your classes, but if you need to strictly validate against an XSD or similar, that should be done separately.

## **Contributing**

Contributions are welcome! If you find issues or have improvements, feel free to open an issue or submit a pull request on the [GitHub repository](https://github.com/owebeeone/xdatatrees).

## **License**

This project is licensed under the LGPL v2.1 (Lesser General Public License v2.1). See the `LICENSE` file in the repository for details.

## **Acknowledgments**

**Xdatatrees** was developed as part of the [**`AnchorSCAD`**](https://github.com/owebeeone/anchorscad-core) project’s needs for robust 3MF (3D Manufacturing Format) file handling. It builds upon the [**`datatrees`**](https://github.com/owebeeone/datatrees) library (also from AnchorSCAD) to provide a comprehensive solution for XML processing, leveraging [**`datatrees`**](https://github.com/owebeeone/datatrees)' features through the `@xdatatree` decorator.