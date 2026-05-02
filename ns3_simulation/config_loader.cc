#include <fstream>
#include <iostream>
#include <string>
#include <vector>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

struct TrafficFlow {
    int src;
    int dst;
    double rate;
};

struct LinkEvent {
    std::string type;
    int src;
    int dst;
    double value;
};

struct ScenarioConfig {
    std::string scenario_id;
    int num_nodes;
    double simulation_time;
    std::vector<TrafficFlow> flows;
    std::vector<LinkEvent> events;
};

ScenarioConfig LoadScenario(std::string scenarioName)
{
    std::string path = "/home/prajwal/cloudroute-ai/scenarios/scenario_" + scenarioName + ".json";

    std::ifstream file(path);
    if (!file)
    {
        std::cout << "ERROR: Cannot open scenario file\n";
        exit(1);
    }

    json j;
    file >> j;

    ScenarioConfig config;

    config.scenario_id = j["scenario_id"];
    config.num_nodes = j["num_nodes"];
    config.simulation_time = j["simulation_time"];

    // Traffic flows
    for (auto &f : j["traffic_flows"])
    {
        config.flows.push_back({
            f["src_node"],
            f["dst_node"],
            f["data_rate_mbps"]
        });
    }

    // Link events
    for (auto &e : j["link_events"])
    {
        LinkEvent ev;
        ev.type = e["type"];
        ev.src = e["link"][0];
        ev.dst = e["link"][1];

        if (e.contains("capacity_mbps"))
            ev.value = e["capacity_mbps"];
        else if (e.contains("time"))
            ev.value = e["time"];
        else
            ev.value = 0.0;

        config.events.push_back(ev);
    }

    std::cout << "✔ Loaded Scenario: " << config.scenario_id << std::endl;
    std::cout << "Nodes: " << config.num_nodes << std::endl;

    return config;
}
