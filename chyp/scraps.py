        #
        # # g = graph_from_json("""
        # # {
        # #   "vertices": {
        # #     "0": {"x": -4, "y": 1},
        # #     "1": {"x": -4, "y": -1},
        # #     "2": {"x": 0, "y": 0},
        # #     "3": {"x": 4, "y": 2},
        # #     "4": {"x": 4, "y": 1},
        # #     "5": {"x": 4, "y": -2}
        # #   },
        # #   "edges": {
        # #     "0": {"s": ["0", "1"], "t": ["2"], "x": -2, "y": 0, "value": "f"},
        # #     "1": {"s": ["2"], "t": ["3", "4", "5"], "x": 2, "y": 0, "value": "g"},
        # #     "2": {"s": ["3"], "t": [], "x": 6, "y": 2, "value": "x"},
        # #     "3": {"s": ["4"], "t": [], "x": 6, "y": 2, "value": "y"}
        # #   },
        # #   "inputs": ["0", "1"],
        # #   "outputs": ["5"]
        # # }
        # # """)
        #
        # g = Graph()
        # v0 = g.add_vertex()
        # v1 = g.add_vertex()
        # v2 = g.add_vertex()
        # v3 = g.add_vertex()
        # v4 = g.add_vertex()
        # v5 = g.add_vertex()
        # # v6 = g.add_vertex()
        # # v0 = g.add_vertex(-4, 1)
        # # v1 = g.add_vertex(-4, -1)
        # # v2 = g.add_vertex(0, 0)
        # # v3 = g.add_vertex(4, 2)
        # # v4 = g.add_vertex(4, 0)
        # # v5 = g.add_vertex(4, -2)
        # g.add_edge([v0, v1], [v2], "f")
        # g.add_edge([v2], [v3,v4,v5], "g")
        # g.add_edge([v3], [], "x")
        # g.add_edge([v4], [], "y")
        # # g.add_edge([v5], [v6], "id")
        # g.set_inputs([v0,v1])
        # g.set_outputs([v5])
        # layer_layout(g)
        #
        # g = Graph()
        # v0 = g.add_vertex()
        # v1 = g.add_vertex()
        # v2 = g.add_vertex()
        # v3 = g.add_vertex()
        # v4 = g.add_vertex()
        # v5 = g.add_vertex()
        # v6 = g.add_vertex()
        # g.add_edge([v0, v1], [v2, v6], "f")
        # g.add_edge([v2], [v3,v4,v5], "g")
        # g.add_edge([v3], [], "x")
        # g.add_edge([v4], [], "q")
        # g.set_inputs([v0,v1])
        # g.set_outputs([v5, v6])
        # layer_layout(g)
        #
        # g1 = Graph()
        # # w0 = g1.add_vertex(0, 0)
        # # w1 = g1.add_vertex(2, 1)
        # # w2 = g1.add_vertex(2, 0)
        # # w3 = g1.add_vertex(2, -1)
        # w0 = g1.add_vertex()
        # w1 = g1.add_vertex()
        # w2 = g1.add_vertex()
        # w3 = g1.add_vertex()
        # g1.add_edge([w0], [w1, w2, w3], "g")
        # g1.add_edge([w1], [], "x")
        # g1.set_inputs([w0])
        # g1.set_outputs([w2, w3])
        # # layer_layout(g1)
        #
        # g2 = Graph()
        # w0 = g2.add_vertex()
        # w1 = g2.add_vertex()
        # w2 = g2.add_vertex()
        # g2.add_edge([w0], [w1, w2], "h")
        # g2.set_inputs([w0])
        # g2.set_outputs([w1, w2])
        #
        # r = Rule(g1, g2)
        #
        # ms = list(match_rule(r, g))
        # if len(ms) != 0:
        #     print(ms[0])
        #     h = rewrite(r, ms[0])
        # else:
        #     print("no matches")
        #     h = g
        #
        # h = h.copy()
        # layer_layout(h)
