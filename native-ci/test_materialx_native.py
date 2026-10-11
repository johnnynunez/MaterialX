"""Native document and CPU shader generation, not GPU rendering."""
import sys
import sysconfig
import unittest
import MaterialX as mx
import MaterialX.PyMaterialXGenShader as gen
import MaterialX.PyMaterialXGenGlsl as glsl


class MaterialXNative(unittest.TestCase):
    def test_native_version(self):
        self.assertEqual(sysconfig.get_platform(), 'win-arm64')
        self.assertEqual(sys.version_info[:2], (3, 12))
        self.assertEqual(mx.getVersionString(), '1.39.5')

    def test_document_roundtrip_and_negative(self):
        doc = mx.createDocument()
        graph = doc.addNodeGraph('native_graph')
        node = graph.addNode('constant', 'color', 'color3')
        node.setInputValue('value', mx.Color3(0.25, 0.5, 0.75), 'color3')
        output = graph.addOutput('out', 'color3')
        output.setConnectedNode(node)
        valid, message = doc.validate()
        self.assertTrue(valid, message)
        text = mx.writeToXmlString(doc)
        copy = mx.createDocument()
        mx.readFromXmlString(copy, text)
        self.assertEqual(mx.writeToXmlString(copy), text)
        self.assertTrue(copy.validate()[0])
        output.setNodeName('missing_node_negative_control')
        self.assertFalse(doc.validate()[0])

    def test_cpu_shader_generation(self):
        doc = mx.createDocument()
        search = mx.getDefaultDataSearchPath()
        loaded = mx.loadLibraries(mx.getDefaultDataLibraryFolders(), search, doc)
        self.assertGreater(len(loaded), 0)
        node = doc.addNode('constant', 'constant_native', 'color3')
        node.setInputValue('value', mx.Color3(0.25, 0.5, 0.75), 'color3')
        output = doc.addOutput('result', 'color3')
        output.setConnectedNode(node)
        self.assertTrue(doc.validate()[0])
        generator = glsl.GlslShaderGenerator.create()
        context = gen.GenContext(generator)
        context.registerSourceCodeSearchPath(search)
        generator.registerTypeDefs(doc)
        shader = generator.generate('native_constant', output, context)
        self.assertIsNotNone(shader)
        code = shader.getSourceCode(gen.PIXEL_STAGE)
        self.assertIn('void main', code)
        self.assertIn('0.25', code)
        self.assertGreater(len(shader.getSourceCode(gen.VERTEX_STAGE)), 0)
        print('CPU GLSL generation bytes:', len(code))


if __name__ == '__main__':
    unittest.main(verbosity=2)
