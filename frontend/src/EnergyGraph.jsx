import React, { useEffect, useState } from "react";
import ForceGraph2D from "react-force-graph-2d";

const EnergyGraph = () => {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const [transactionDecisions, setTransactionDecisions] = useState({});

  const getColor = (status, id = "") => {
    const s = (status || "").toLowerCase();

    if (id === "grid") return "#BDBDBD"; // will be overridden later

    if (s.includes("buying from grid") || s.includes("charging from grid")) return "#E53935";
    if (s.includes("selling to grid")) return "#8E24AA";

    if (s.includes("community battery")) {
      if (s.includes("selling")) return "#FB8C00";
      if (s.includes("buying") || s.includes("using")) return "#FDD835";
      if (s.includes("charging")) return "#00ACC1";
    }

    if (id && (id.startsWith("rc") || id.startsWith("cc"))) {
      if (s.includes("buying")) return "#1E88E5";
      if (s.includes("selling")) return "#43A047";
    }

    if (s.includes("community pv")) return "#7CB342";

    return "#BDBDBD"; // default
  };

  const fetchData = async () => {
    try {
      const response = await fetch("http://localhost:5000/optimize");
      const data = await response.json();

      const decisions = data.transaction_decisions || {};
      setTransactionDecisions(decisions);

      const nodeIds = [
        "rcwopv1",
        "rcwopv2",
        "rcwpv1",
        "rcwpv2",
        "ccwopv",
        "ccwpv",
        "cpv",
        "cbat",
        "grid",
      ];

      let links = [];

      // === Grid, PV, Battery logic ===
      Object.entries(decisions).forEach(([entity, decision]) => {
        const lowerDecision = decision.toLowerCase();

        if (lowerDecision.includes("buying from grid")) {
          links.push({ source: "grid", target: entity });
        }

        if (lowerDecision.includes("selling to grid")) {
          links.push({ source: entity, target: "grid" });
        }

        if (
          lowerDecision.includes("buying from community battery") ||
          lowerDecision.includes("using community battery")
        ) {
          links.push({ source: "cbat", target: entity });
        }

        if (
          lowerDecision.includes("selling to community battery") ||
          lowerDecision.includes("charging community battery")
        ) {
          links.push({ source: entity, target: "cbat" });
        }

        if (lowerDecision.includes("buying from community pv")) {
          links.push({ source: "cpv", target: entity });
        }

        if (lowerDecision.includes("charging community battery")) {
          links.push({ source: "cpv", target: "cbat" });
        }
      });

      // === Unique customer-to-customer matching logic ===
      const availableSellers = new Set(Object.keys(decisions).filter((entity) =>
        decisions[entity]?.toLowerCase().includes("selling to residential") ||
        decisions[entity]?.toLowerCase().includes("selling to commercial")
      ));

      const matchedSellers = new Set();

      Object.entries(decisions).forEach(([buyer, decision]) => {
        const lowerDecision = decision.toLowerCase();

        if (lowerDecision.includes("buying from residential") || lowerDecision.includes("buying from commercial")) {
          for (let seller of availableSellers) {
            if (!matchedSellers.has(seller)) {
              links.push({ source: seller, target: buyer });
              matchedSellers.add(seller);
              break;
            }
          }
        }
      });

      // === Fallback: Unmatched sellers → CBAT or grid ===
      availableSellers.forEach((seller) => {
        if (!matchedSellers.has(seller)) {
          const originalDecision = decisions[seller] || "";
          const lower = originalDecision.toLowerCase();
      
          if (lower.includes("community battery")) {
            links.push({ source: seller, target: "cbat" });
            decisions[seller] = `${originalDecision} → No buyer available → Selling to Community Battery`;
          } else {
            links.push({ source: seller, target: "grid" });
            decisions[seller] = `${originalDecision} → No buyer available → Selling to Grid`;
          }
      
          matchedSellers.add(seller);
        }
      });
      

      // === Fallback: Unmatched buyers → CBAT, CPV, or grid ===
      const buyersWantingCustomerEnergy = Object.entries(decisions)
        .filter(([entity, decision]) =>
          decision?.toLowerCase().includes("buying from residential") ||
          decision?.toLowerCase().includes("buying from commercial")
        )
        .map(([entity]) => entity);

      const matchedBuyers = new Set(links.map(link => link.target));

      buyersWantingCustomerEnergy.forEach((buyer) => {
        if (!matchedBuyers.has(buyer)) {
          const originalDecision = decisions[buyer] || "";
          const lower = originalDecision.toLowerCase();
      
          if (lower.includes("community battery")) {
            links.push({ source: "cbat", target: buyer });
            decisions[buyer] = `${originalDecision} → No seller available → Buying from Community Battery`;
          } else if (lower.includes("community pv")) {
            links.push({ source: "cpv", target: buyer });
            decisions[buyer] = `${originalDecision} → No seller available → Buying from Community PV`;
          } else {
            links.push({ source: "grid", target: buyer });
            decisions[buyer] = `${originalDecision} → No seller available → Buying from Grid`;
          }
        }
      });
      

      // === Nodes with dynamic grid color ===
      const nodes = nodeIds.map((id) => {
        if (id === "grid") {
          const isSelling = links.some(link => link.source === "grid");
          const isBuying = links.some(link => link.target === "grid");

          return {
            id,
            color: isSelling ? "#8E24AA" : isBuying ? "#E53935" : "#BDBDBD"
          };
        }

        return {
          id,
          color: getColor(decisions[id], id)
        };
      });

      setGraphData({ nodes, links });
    } catch (err) {
      console.error("Error fetching graph data:", err);
    }
  };

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div style={{ display: "flex", height: "100vh", width: "100%", overflow: "hidden" }}>
      <div style={{ flex: 3, overflow: "hidden" }}>
        <ForceGraph2D
          graphData={graphData}
          nodeAutoColorBy={null}
          nodeLabel="id"
          linkDirectionalParticles={2}
          linkDirectionalParticleSpeed={0.01}
          linkDirectionalArrowLength={5}
          linkDirectionalArrowRelPos={1}
          linkColor={() => "#666"}
          linkLabel={(link) => `${link.source} → ${link.target}`}
          nodeCanvasObjectMode={() => "after"}
          nodeCanvasObject={(node, ctx) => {
            const label = node.id;
            const fontSize = 10;
            ctx.font = `${fontSize}px Sans-Serif`;
            ctx.fillStyle = "black";
            ctx.textAlign = "center";
            ctx.fillText(label, node.x, node.y + 10);
          }}
          nodeColor={(node) => node.color || "#BDBDBD"}
        />
      </div>

      <div style={{
        width: "300px",
        padding: "10px",
        overflowY: "auto",
        backgroundColor: "#f5f5f5",
        borderLeft: "1px solid #ccc"
      }}>
        <h3>Transaction Decisions</h3>
        <ul style={{ listStyle: "none", padding: 0, fontSize: "14px", lineHeight: "1.6em" }}>
          {Object.entries(transactionDecisions).map(([entity, decision]) => (
            <li key={entity}>
              <strong>{entity}:</strong> {decision}
            </li>
          ))}
        </ul>

        <h3>Legend</h3>
        <ul style={{ listStyle: "none", padding: 0, fontSize: "14px", lineHeight: "1.6em" }}>
          <li><span style={{ color: "#E53935", fontWeight: "bold" }}>■</span> Buying from Grid</li>
          <li><span style={{ color: "#8E24AA", fontWeight: "bold" }}>■</span> Selling to Grid/Retailer</li>
          <li><span style={{ color: "#FDD835", fontWeight: "bold" }}>■</span> Buying from Battery</li>
          <li><span style={{ color: "#FB8C00", fontWeight: "bold" }}>■</span> Selling to Battery</li>
          <li><span style={{ color: "#00ACC1", fontWeight: "bold" }}>■</span> Charging Battery</li>
          <li><span style={{ color: "#7CB342", fontWeight: "bold" }}>■</span> Community PV</li>
          <li><span style={{ color: "#1E88E5", fontWeight: "bold" }}>■</span> Buying (Customer)</li>
          <li><span style={{ color: "#43A047", fontWeight: "bold" }}>■</span> Selling (Customer)</li>
        </ul>
      </div>
    </div>
  );
};

export default EnergyGraph;
