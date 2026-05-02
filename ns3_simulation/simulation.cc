#include "ns3/core-module.h"
#include "ns3/network-module.h"
#include "ns3/internet-module.h"
#include "ns3/point-to-point-module.h"
#include "ns3/applications-module.h"
#include "ns3/netanim-module.h"
#include "ns3/flow-monitor-module.h"

using namespace ns3;

int main(int argc, char *argv[])
{
    std::string scenario = "normal";

    CommandLine cmd;
    cmd.AddValue("scenario", "Scenario type", scenario);
    cmd.Parse(argc, argv);

    std::cout << "Running Scenario: " << scenario << std::endl;

    NodeContainer nodes;
    nodes.Create(8);

    InternetStackHelper stack;
    stack.Install(nodes);

    PointToPointHelper p2p;

    if (scenario == "congestion")
        p2p.SetDeviceAttribute("DataRate", StringValue("2Mbps"));
    else
        p2p.SetDeviceAttribute("DataRate", StringValue("10Mbps"));

    p2p.SetChannelAttribute("Delay", StringValue("2ms"));

    NetDeviceContainer devices[7];

    for (int i = 0; i < 7; i++)
    {
        devices[i] = p2p.Install(nodes.Get(i), nodes.Get(i + 1));
    }

    Ipv4AddressHelper address;
    Ipv4InterfaceContainer interfaces[7];

    for (int i = 0; i < 7; i++)
    {
        std::ostringstream subnet;
        subnet << "10.1." << i + 1 << ".0";

        address.SetBase(subnet.str().c_str(), "255.255.255.0");
        interfaces[i] = address.Assign(devices[i]);
    }

    Ipv4GlobalRoutingHelper::PopulateRoutingTables();

    uint16_t port = 9;

    OnOffHelper onoff("ns3::UdpSocketFactory",
                      Address(InetSocketAddress(interfaces[6].GetAddress(1), port)));

    onoff.SetConstantRate(DataRate("1Mbps"));

    if (scenario == "congestion")
        onoff.SetConstantRate(DataRate("5Mbps"));

    ApplicationContainer app = onoff.Install(nodes.Get(0));
    app.Start(Seconds(1.0));
    app.Stop(Seconds(10.0));

    PacketSinkHelper sink("ns3::UdpSocketFactory",
                          InetSocketAddress(Ipv4Address::GetAny(), port));

    sink.Install(nodes.Get(7));

    FlowMonitorHelper flowHelper;
    Ptr<FlowMonitor> monitor = flowHelper.InstallAll();

    AnimationInterface anim("animation.xml");

    for (uint32_t i = 0; i < 8; i++)
    {
        anim.SetConstantPosition(nodes.Get(i), i * 20, 50);
    }

    std::cout << "Simulation Started..." << std::endl;

    Simulator::Stop(Seconds(10.0));
    Simulator::Run();

    monitor->SerializeToXmlFile("flowmon.xml", true, true);

    Simulator::Destroy();

    std::cout << "Simulation Finished!" << std::endl;

    return 0;
}
