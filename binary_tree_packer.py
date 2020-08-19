"""
This code is adapted from https://github.com/jakesgordon/bin-packing/

Copyright (c) 2011, 2012, 2013, 2014, 2015, 2016 Jake Gordon and contributors
Copyright (c) 2020 Sebastian "Chloride Cull" Johansson

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

from typing import List, Optional


class NodePackerItem:
    def __init__(self, identity: str, w: int, h: int):
        self.identity = identity
        self.w = w
        self.h = h
        self.fit: Optional[Node] = None


class Node:
    def __init__(self, x: int, y: int, w: int, h: int):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.used = False
        self.down: Optional[Node] = None
        self.right: Optional[Node] = None


class PackerResult:
    def __init__(self, w: int, h: int, items: List[NodePackerItem]):
        self.w = w
        self.h = h
        self.items = items


class Packer:
    def __init__(self):
        self.root: Optional[Node] = None

    def fit(self, blocks: List[NodePackerItem]):
        self.root = Node(0, 0, blocks[0].w, blocks[0].h)
        for block in blocks:
            node = self.find_node(self.root, block.w, block.h)
            if node is not None:
                block.fit = self.split_node(node, block.w, block.h)
            else:
                block.fit = self.grow_node(block.w, block.h)

    def find_node(self, root: Node, w: int, h: int):
        if root.used:
            candidate_node = self.find_node(root.right, w, h)
            if candidate_node is None:
                candidate_node = self.find_node(root.down, w, h)
            return candidate_node
        elif w <= root.w and h <= root.h:
            return root
        return None

    def split_node(self, node: Node, w: int, h: int):
        node.used = True
        node.down = Node(node.x, node.y + h, node.w, node.h - h)
        node.right = Node(node.x + w, node.y, node.w - w, h)
        return node

    def grow_node(self, w: int, h: int):
        can_grow_down = w <= self.root.w
        can_grow_right = h <= self.root.h
        should_grow_right = can_grow_right and (self.root.h >= (self.root.w + w))
        should_grow_down = can_grow_down and (self.root.w >= (self.root.h + h))

        if should_grow_right:
            return self.grow_right(w, h)
        if should_grow_down:
            return self.grow_down(w, h)
        if can_grow_right:
            return self.grow_right(w, h)
        if can_grow_down:
            return self.grow_down(w, h)
        return None

    def grow_right(self, w: int, h: int):
        new_root = Node(0, 0, self.root.w + w, self.root.h)
        new_root.used = True
        new_root.down = self.root
        new_root.right = Node(self.root.w, 0, w, self.root.h)
        self.root = new_root

        node = self.find_node(self.root, w, h)
        if node is not None:
            return self.split_node(node, w, h)
        return None

    def grow_down(self, w: int, h: int):
        new_root = Node(0, 0, self.root.w, self.root.h + h)
        new_root.used = True
        new_root.down = Node(0, self.root.h, self.root.w, h)
        new_root.right = self.root
        self.root = new_root

        node = self.find_node(self.root, w, h)
        if node is not None:
            return self.split_node(node, w, h)
        return None


def pack_items_binary_tree(items: List[NodePackerItem]):
    sorted_items = sorted(items, key=lambda x: x.w if x.w > x.h else x.h, reverse=True)

    packer = Packer()
    packer.fit(sorted_items)

    return PackerResult(packer.root.w, packer.root.h, sorted_items)
