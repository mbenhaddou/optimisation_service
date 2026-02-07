"use client";

import { useMemo, useState, useEffect, useRef } from "react";

const defaultApiBase =
  process.env.NEXT_PUBLIC_API_BASE ?? "http://localhost:8000";
const osrmBase = process.env.NEXT_PUBLIC_OSRM_BASE ?? "";

const SETTINGS_KEY = "optimise.portal.settings";
const API_KEY_STORAGE = "optimise.portal.apiKey";
const SCENARIOS_KEY = "optimise.portal.scenarios";
const LEAFLET_JS_URL = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js";
const LEAFLET_CSS_URL = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css";
const ROUTE_COLORS = ["#f97316", "#0ea5e9", "#14b8a6", "#a855f7"];

type VehicleForm = {
  id: string;
  startLat: string;
  startLng: string;
  endLat: string;
  endLng: string;
  windowStart: string;
  windowEnd: string;
  breakStart: string;
  breakEnd: string;
  breakDuration: string;
  maxTasks: string;
  skills: string;
  depotId: string;
  teamId: string;
};

type TaskForm = {
  id: string;
  type: string;
  lat: string;
  lng: string;
  serviceDuration: string;
  windowStart: string;
  windowEnd: string;
  preferredWindowStart: string;
  preferredWindowEnd: string;
  softPenalty: string;
  priority: string;
  requiredSkills: string;
};

type DepotForm = {
  id: string;
  name: string;
  lat: string;
  lng: string;
  address: string;
  windowStart: string;
  windowEnd: string;
};

type PlannerScenarioData = {
  problemType: string;
  primaryObjective: string;
  secondaryObjective: string;
  windowStart: string;
  windowEnd: string;
  vehicles: VehicleForm[];
  tasks: TaskForm[];
  depots: DepotForm[];
  maxRouteDuration: string;
  maxRouteDistance: string;
  balanceRoutes: boolean;
  allowOvertime: boolean;
  maxCompute: string;
  solutionQuality: string;
  returnAlternatives: string;
  calculateCarbon: boolean;
};

type SavedScenario = {
  id: string;
  name: string;
  savedAt: string;
  data: PlannerScenarioData;
};

const createVehicle = (index: number): VehicleForm => ({
  id: `vehicle_${index}`,
  startLat: "",
  startLng: "",
  endLat: "",
  endLng: "",
  windowStart: "",
  windowEnd: "",
  breakStart: "",
  breakEnd: "",
  breakDuration: "30",
  maxTasks: "50",
  skills: "",
  depotId: "",
  teamId: "",
});

const createTask = (index: number): TaskForm => ({
  id: `task_${index}`,
  type: "delivery",
  lat: "",
  lng: "",
  serviceDuration: "10",
  windowStart: "",
  windowEnd: "",
  preferredWindowStart: "",
  preferredWindowEnd: "",
  softPenalty: "",
  priority: "3",
  requiredSkills: "",
});

const createDepot = (index: number): DepotForm => ({
  id: `depot_${index}`,
  name: "",
  lat: "",
  lng: "",
  address: "",
  windowStart: "",
  windowEnd: "",
});

const pad2 = (value: number) => String(value).padStart(2, "0");

const formatLocalInput = (date: Date) =>
  `${date.getFullYear()}-${pad2(date.getMonth() + 1)}-${pad2(
    date.getDate()
  )}T${pad2(date.getHours())}:${pad2(date.getMinutes())}`;

const formatDateTime = (value: string) => {
  if (!value) return "";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "";
  return parsed.toISOString();
};

const parseCsv = (value: string) =>
  value
    .split(",")
    .map((entry) => entry.trim())
    .filter(Boolean);

const buildSampleScenario = (): PlannerScenarioData => {
  const now = new Date();
  const start = new Date(now);
  start.setHours(8, 0, 0, 0);
  const end = new Date(now);
  end.setHours(17, 0, 0, 0);
  const windowStart = formatLocalInput(start);
  const windowEnd = formatLocalInput(end);

  const depotLat = "50.8476";
  const depotLng = "4.3561";

  return {
    problemType: "vrptw",
    primaryObjective: "minimize_total_duration",
    secondaryObjective: "minimize_total_distance",
    windowStart,
    windowEnd,
    vehicles: [
      {
        id: "van_1",
        startLat: depotLat,
        startLng: depotLng,
        endLat: depotLat,
        endLng: depotLng,
        windowStart: "",
        windowEnd: "",
        breakStart: "",
        breakEnd: "",
        breakDuration: "30",
        maxTasks: "4",
        skills: "delivery, pickup",
        depotId: "brussels_depot",
        teamId: "brussels_team",
      },
      {
        id: "van_2",
        startLat: depotLat,
        startLng: depotLng,
        endLat: depotLat,
        endLng: depotLng,
        windowStart: "",
        windowEnd: "",
        breakStart: "",
        breakEnd: "",
        breakDuration: "30",
        maxTasks: "4",
        skills: "delivery",
        depotId: "brussels_depot",
        teamId: "brussels_team",
      },
    ],
    tasks: [
      {
        id: "task_1",
        type: "delivery",
        lat: "50.8466",
        lng: "4.3528",
        serviceDuration: "15",
        windowStart: "",
        windowEnd: "",
        preferredWindowStart: "",
        preferredWindowEnd: "",
        softPenalty: "",
        priority: "2",
        requiredSkills: "delivery",
      },
      {
        id: "task_2",
        type: "delivery",
        lat: "50.8503",
        lng: "4.3517",
        serviceDuration: "20",
        windowStart: "",
        windowEnd: "",
        preferredWindowStart: "",
        preferredWindowEnd: "",
        softPenalty: "",
        priority: "3",
        requiredSkills: "delivery",
      },
      {
        id: "task_3",
        type: "pickup",
        lat: "50.8429",
        lng: "4.3572",
        serviceDuration: "10",
        windowStart: "",
        windowEnd: "",
        preferredWindowStart: "",
        preferredWindowEnd: "",
        softPenalty: "",
        priority: "4",
        requiredSkills: "pickup",
      },
      {
        id: "task_4",
        type: "delivery",
        lat: "50.8520",
        lng: "4.3696",
        serviceDuration: "15",
        windowStart: "",
        windowEnd: "",
        preferredWindowStart: "",
        preferredWindowEnd: "",
        softPenalty: "",
        priority: "3",
        requiredSkills: "delivery",
      },
      {
        id: "task_5",
        type: "delivery",
        lat: "50.8553",
        lng: "4.3488",
        serviceDuration: "12",
        windowStart: "",
        windowEnd: "",
        preferredWindowStart: "",
        preferredWindowEnd: "",
        softPenalty: "",
        priority: "2",
        requiredSkills: "delivery",
      },
    ],
    depots: [
      {
        id: "brussels_depot",
        name: "Brussels Depot",
        lat: depotLat,
        lng: depotLng,
        address: "Rue Ravenstein 2, 1000 Brussels",
        windowStart: "",
        windowEnd: "",
      },
    ],
    maxRouteDuration: "480",
    maxRouteDistance: "120",
    balanceRoutes: true,
    allowOvertime: false,
    maxCompute: "20",
    solutionQuality: "balanced",
    returnAlternatives: "0",
    calculateCarbon: false,
  };
};

export default function PlannerPage() {
  const [apiBase, setApiBase] = useState(defaultApiBase);
  const [apiKey, setApiKey] = useState("");
  const [step, setStep] = useState(1);
  const sampleScenario = useMemo(() => buildSampleScenario(), []);
  const [scenarioName, setScenarioName] = useState("");
  const [savedScenarios, setSavedScenarios] = useState<SavedScenario[]>([]);
  const [selectedScenarioId, setSelectedScenarioId] = useState("");
  const [plannerNotice, setPlannerNotice] = useState("");
  const mapRef = useRef<HTMLDivElement | null>(null);
  const mapInstanceRef = useRef<any>(null);
  const mapLayerRef = useRef<any>(null);
  const osrmCacheRef = useRef<Map<string, any>>(new Map());
  const [osrmRouteMetrics, setOsrmRouteMetrics] = useState<
    Record<string, { distanceKm: number; durationMin: number }>
  >({});

  const [problemType, setProblemType] = useState("vrptw");
  const [primaryObjective, setPrimaryObjective] = useState(
    "minimize_total_duration"
  );
  const [secondaryObjective, setSecondaryObjective] = useState(
    "minimize_total_distance"
  );
  const [windowStart, setWindowStart] = useState("");
  const [windowEnd, setWindowEnd] = useState("");

  const [vehicles, setVehicles] = useState<VehicleForm[]>([createVehicle(1)]);
  const [tasks, setTasks] = useState<TaskForm[]>([createTask(1)]);
  const [depots, setDepots] = useState<DepotForm[]>([createDepot(1)]);

  const [maxRouteDuration, setMaxRouteDuration] = useState("480");
  const [maxRouteDistance, setMaxRouteDistance] = useState("200");
  const [balanceRoutes, setBalanceRoutes] = useState(true);
  const [allowOvertime, setAllowOvertime] = useState(false);
  const [maxCompute, setMaxCompute] = useState("30");
  const [solutionQuality, setSolutionQuality] = useState("balanced");
  const [returnAlternatives, setReturnAlternatives] = useState("0");
  const [calculateCarbon, setCalculateCarbon] = useState(false);

  const [responseRaw, setResponseRaw] = useState("");
  const [responseParsed, setResponseParsed] = useState<any>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const storedKey = window.localStorage.getItem(API_KEY_STORAGE);
    if (storedKey) setApiKey(storedKey);
    const settingsRaw = window.localStorage.getItem(SETTINGS_KEY);
    if (settingsRaw) {
      try {
        const stored = JSON.parse(settingsRaw);
        if (stored.apiBase) setApiBase(stored.apiBase);
      } catch (err) {
        console.warn("Failed to parse settings", err);
      }
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (apiKey.trim()) {
      window.localStorage.setItem(API_KEY_STORAGE, apiKey.trim());
    }
  }, [apiKey]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    const raw = window.localStorage.getItem(SCENARIOS_KEY);
    if (!raw) return;
    try {
      const parsed = JSON.parse(raw) as SavedScenario[];
      if (Array.isArray(parsed)) {
        setSavedScenarios(parsed);
      }
    } catch (err) {
      console.warn("Failed to parse saved scenarios", err);
    }
  }, []);

  useEffect(() => {
    if (typeof window === "undefined") return;
    window.localStorage.setItem(SCENARIOS_KEY, JSON.stringify(savedScenarios));
  }, [savedScenarios]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    if (step !== 3) return;
    if (!mapRef.current) return;
    if (mapInstanceRef.current) {
      mapInstanceRef.current.invalidateSize?.();
      return;
    }

    const ensureLeaflet = () =>
      new Promise<any>((resolve, reject) => {
        if ((window as any).L) {
          resolve((window as any).L);
          return;
        }

        const existingScript = document.querySelector(
          `script[src="${LEAFLET_JS_URL}"]`
        );
        if (!document.querySelector(`link[href="${LEAFLET_CSS_URL}"]`)) {
          const link = document.createElement("link");
          link.rel = "stylesheet";
          link.href = LEAFLET_CSS_URL;
          document.head.appendChild(link);
        }

        if (existingScript) {
          existingScript.addEventListener("load", () =>
            resolve((window as any).L)
          );
          return;
        }

        const script = document.createElement("script");
        script.src = LEAFLET_JS_URL;
        script.async = true;
        script.onload = () => resolve((window as any).L);
        script.onerror = () => reject(new Error("Failed to load map library"));
        document.body.appendChild(script);
      });

    ensureLeaflet()
      .then((L) => {
        if (!mapRef.current || mapInstanceRef.current) return;
        const map = L.map(mapRef.current, {
          zoomControl: true,
          scrollWheelZoom: false,
        }).setView([50.8476, 4.3561], 12);
        L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
          attribution: "© OpenStreetMap contributors",
        }).addTo(map);
        mapInstanceRef.current = map;
        mapLayerRef.current = L.layerGroup().addTo(map);
      })
      .catch((err) => {
        console.warn(err);
      });
  }, [step]);

  useEffect(() => {
    if (!mapInstanceRef.current || !mapLayerRef.current) return;
    const L = (window as any).L;
    if (!L) return;

    const layerGroup = mapLayerRef.current;
    layerGroup.clearLayers();
    setOsrmRouteMetrics({});

    const routeStops = responseParsed?.routes?.map((route: any) =>
      route.stops?.map((stop: any) => ({
        lat: stop.location?.lat,
        lng: stop.location?.lng,
        type: stop.type,
      }))
    );

    const drawStopMarkers = (stops: any[], color: string) => {
      stops.forEach((stop, idx) => {
        if (!Number.isFinite(stop.lat) || !Number.isFinite(stop.lng)) return;
        const icon = L.divIcon({
          className: "planner-stop-marker",
          html: `<span style="border-color:${color}">${idx + 1}</span>`,
          iconSize: [26, 26],
          iconAnchor: [13, 13],
        });
        L.marker([Number(stop.lat), Number(stop.lng)], { icon }).addTo(layerGroup);
      });
    };

    const drawStraightLines = () => {
      routeStops?.forEach((stops: any[], idx: number) => {
        const points: [number, number][] = stops
          .filter((stop) => Number.isFinite(stop.lat) && Number.isFinite(stop.lng))
          .map((stop) => [Number(stop.lat), Number(stop.lng)]);
        if (points.length === 0) return;
        L.polyline(points, {
          color: ROUTE_COLORS[idx % ROUTE_COLORS.length],
          weight: 4,
          opacity: 0.8,
        }).addTo(layerGroup);
        drawStopMarkers(stops, ROUTE_COLORS[idx % ROUTE_COLORS.length]);
      });
    };

    const drawOsrmRoutes = async () => {
      if (!osrmBase || !routeStops || routeStops.length === 0) return false;

      const results = await Promise.all(
        routeStops.map(async (stops: any[], idx: number) => {
          const coords = stops
            .filter((stop) => Number.isFinite(stop.lat) && Number.isFinite(stop.lng))
            .map((stop) => `${Number(stop.lng)},${Number(stop.lat)}`)
            .join(";");
          if (!coords || coords.split(";").length < 2) return null;

          const url = `${osrmBase.replace(/\/$/, "")}/route/v1/driving/${coords}?overview=full&geometries=geojson`;
          try {
            const cached = osrmCacheRef.current.get(url);
            const data = cached ?? (await (async () => {
              const res = await fetch(url);
              if (!res.ok) return null;
              return res.json();
            })());
            if (!data) return null;
            if (!cached) {
              osrmCacheRef.current.set(url, data);
            }
            const geometry = data?.routes?.[0]?.geometry;
            const distance = data?.routes?.[0]?.distance;
            const duration = data?.routes?.[0]?.duration;
            if (!geometry?.coordinates) return null;
            return {
              geometry,
              color: ROUTE_COLORS[idx % ROUTE_COLORS.length],
              distance,
              duration,
            };
          } catch {
            return null;
          }
        })
      );

      const anyRoute = results.some((item) => item);
      const metrics: Record<string, { distanceKm: number; durationMin: number }> = {};
      results.forEach((item, idx) => {
        if (!item) return;
        const coords = item.geometry.coordinates.map(
          (pair: [number, number]) => [pair[1], pair[0]]
        );
        L.polyline(coords, {
          color: item.color,
          weight: 4,
          opacity: 0.85,
        }).addTo(layerGroup);

        // Draw simple direction arrows along the route.
        const arrowEvery = Math.max(8, Math.floor(coords.length / 8));
        for (let i = arrowEvery; i < coords.length; i += arrowEvery) {
          const prev = coords[i - 1];
          const curr = coords[i];
          if (!prev || !curr) continue;
          const angle =
            (Math.atan2(curr[0] - prev[0], curr[1] - prev[1]) * 180) / Math.PI;
          const icon = L.divIcon({
            className: "planner-route-arrow",
            html: `<span style="transform: rotate(${angle}deg)">></span>`,
            iconSize: [18, 18],
            iconAnchor: [9, 9],
          });
          L.marker(curr, { icon }).addTo(layerGroup);
        }
        const route = responseParsed?.routes?.[idx];
        if (
          route?.vehicle_id &&
          Number.isFinite(item.distance) &&
          Number.isFinite(item.duration)
        ) {
          metrics[route.vehicle_id] = {
            distanceKm: Number(item.distance) / 1000,
            durationMin: Number(item.duration) / 60,
          };
        }
        if (routeStops?.[idx]) {
          drawStopMarkers(routeStops[idx], item.color);
        }
      });

      if (Object.keys(metrics).length > 0) {
        setOsrmRouteMetrics(metrics);
      }

      return anyRoute;
    };

    const drawPreview = () => {
      const previewPoints: [number, number][] = [];
      vehicles.forEach((vehicle) => {
        const lat = Number(vehicle.startLat);
        const lng = Number(vehicle.startLng);
        if (Number.isFinite(lat) && Number.isFinite(lng)) {
          previewPoints.push([lat, lng]);
          L.circleMarker([lat, lng], {
            radius: 6,
            color: "#0f172a",
            fillOpacity: 0.7,
          }).addTo(layerGroup);
        }
      });
      tasks.forEach((task) => {
        const lat = Number(task.lat);
        const lng = Number(task.lng);
        if (Number.isFinite(lat) && Number.isFinite(lng)) {
          previewPoints.push([lat, lng]);
          L.circleMarker([lat, lng], {
            radius: 5,
            color: "#f97316",
            fillOpacity: 0.8,
          }).addTo(layerGroup);
        }
      });
      if (previewPoints.length > 1) {
        L.polyline(previewPoints, {
          color: "#94a3b8",
          weight: 2,
          dashArray: "4 6",
        }).addTo(layerGroup);
      }
    };

    (async () => {
      if (routeStops && routeStops.length > 0) {
        const drewOsrm = await drawOsrmRoutes();
        if (!drewOsrm) {
          drawStraightLines();
        }
      } else {
        drawPreview();
      }

      const bounds = layerGroup.getBounds?.();
      if (bounds && bounds.isValid()) {
        mapInstanceRef.current.fitBounds(bounds.pad(0.2));
      }
    })();

  }, [responseParsed, vehicles, tasks]);

  const payload = useMemo(() => {
    const defaultStart = formatDateTime(windowStart);
    const defaultEnd = formatDateTime(windowEnd);

    const formattedVehicles = vehicles.map((vehicle) => {
      const startLat = Number(vehicle.startLat || 0);
      const startLng = Number(vehicle.startLng || 0);
      const endLat = Number(vehicle.endLat || vehicle.startLat || 0);
      const endLng = Number(vehicle.endLng || vehicle.startLng || 0);
      const vehicleStart = formatDateTime(vehicle.windowStart) || defaultStart;
      const vehicleEnd = formatDateTime(vehicle.windowEnd) || defaultEnd;
      const breakStart = formatDateTime(vehicle.breakStart);
      const breakEnd =
        formatDateTime(vehicle.breakEnd) ||
        (breakStart && vehicle.breakDuration
          ? new Date(
              new Date(breakStart).getTime() +
                Number(vehicle.breakDuration) * 60000
            ).toISOString()
          : "");

      return {
        id: vehicle.id,
        start_location: { lat: startLat, lng: startLng },
        end_location: { lat: endLat, lng: endLng },
        capacity: { weight: 1000 },
        available_time_windows: vehicleStart && vehicleEnd ? [
          { start: vehicleStart, end: vehicleEnd },
        ] : [],
        breaks:
          breakStart && breakEnd
            ? [
                {
                  duration_minutes: Number(vehicle.breakDuration || 30),
                  time_window: { earliest: breakStart, latest: breakEnd },
                },
              ]
            : [],
        max_tasks: Number(vehicle.maxTasks || 0) || undefined,
        skills: parseCsv(vehicle.skills),
        depot_id: vehicle.depotId || undefined,
        team_id: vehicle.teamId || undefined,
      };
    });

    const formattedTasks = tasks.map((task) => {
      const taskStart = formatDateTime(task.windowStart) || defaultStart;
      const taskEnd = formatDateTime(task.windowEnd) || defaultEnd;
      const preferredStart =
        formatDateTime(task.preferredWindowStart) || "";
      const preferredEnd = formatDateTime(task.preferredWindowEnd) || "";
      return {
        id: task.id,
        type: task.type,
        location: { lat: Number(task.lat || 0), lng: Number(task.lng || 0) },
        service_duration_minutes: Number(task.serviceDuration || 10),
        time_windows:
          taskStart && taskEnd ? [{ start: taskStart, end: taskEnd }] : [],
        preferred_time_windows:
          preferredStart && preferredEnd
            ? [{ start: preferredStart, end: preferredEnd }]
            : [],
        soft_time_window_penalty: task.softPenalty
          ? Number(task.softPenalty)
          : undefined,
        demand: { weight: 1 },
        priority: Number(task.priority || 3),
        required_skills: parseCsv(task.requiredSkills),
      };
    });

    const formattedDepots = depots.map((depot) => {
      const depotStart = formatDateTime(depot.windowStart) || defaultStart;
      const depotEnd = formatDateTime(depot.windowEnd) || defaultEnd;
      return {
        id: depot.id,
        name: depot.name || undefined,
        location: { lat: Number(depot.lat || 0), lng: Number(depot.lng || 0), address: depot.address || undefined },
        time_windows: depotStart && depotEnd ? [{ start: depotStart, end: depotEnd }] : [],
      };
    });

    return {
      problem_type: problemType,
      objectives: {
        primary: primaryObjective,
        secondary: secondaryObjective,
        weights: {
          duration: 0.7,
          distance: 0.3,
        },
      },
      vehicles: formattedVehicles,
      tasks: formattedTasks,
      depots: formattedDepots,
      constraints: {
        max_route_duration_minutes: Number(maxRouteDuration || 0) || undefined,
        max_route_distance_km: Number(maxRouteDistance || 0) || undefined,
        balance_routes: balanceRoutes,
        allow_overtime: allowOvertime,
      },
      optimization: {
        max_computation_time_seconds: Number(maxCompute || 0) || undefined,
        solution_quality: solutionQuality,
        return_alternative_solutions: Number(returnAlternatives || 0) || undefined,
      },
      options: {
        return_detailed_metrics: true,
        include_route_geometry: false,
        calculate_carbon_footprint: calculateCarbon,
      },
    };
  }, [
    problemType,
    primaryObjective,
    secondaryObjective,
    windowStart,
    windowEnd,
    vehicles,
    tasks,
    depots,
    maxRouteDuration,
    maxRouteDistance,
    balanceRoutes,
    allowOvertime,
    maxCompute,
    solutionQuality,
    returnAlternatives,
    calculateCarbon,
  ]);

  const captureScenario = (): PlannerScenarioData => ({
    problemType,
    primaryObjective,
    secondaryObjective,
    windowStart,
    windowEnd,
    vehicles,
    tasks,
    depots,
    maxRouteDuration,
    maxRouteDistance,
    balanceRoutes,
    allowOvertime,
    maxCompute,
    solutionQuality,
    returnAlternatives,
    calculateCarbon,
  });

  const applyScenario = (data: PlannerScenarioData) => {
    setProblemType(data.problemType || "vrptw");
    setPrimaryObjective(data.primaryObjective || "minimize_total_duration");
    setSecondaryObjective(data.secondaryObjective || "minimize_total_distance");
    setWindowStart(data.windowStart || "");
    setWindowEnd(data.windowEnd || "");
    setVehicles(data.vehicles?.length ? data.vehicles : [createVehicle(1)]);
    setTasks(data.tasks?.length ? data.tasks : [createTask(1)]);
    setDepots(data.depots?.length ? data.depots : [createDepot(1)]);
    setMaxRouteDuration(data.maxRouteDuration || "480");
    setMaxRouteDistance(data.maxRouteDistance || "200");
    setBalanceRoutes(
      typeof data.balanceRoutes === "boolean" ? data.balanceRoutes : true
    );
    setAllowOvertime(
      typeof data.allowOvertime === "boolean" ? data.allowOvertime : false
    );
    setMaxCompute(data.maxCompute || "30");
    setSolutionQuality(data.solutionQuality || "balanced");
    setReturnAlternatives(data.returnAlternatives || "0");
    setCalculateCarbon(
      typeof data.calculateCarbon === "boolean" ? data.calculateCarbon : false
    );
    setResponseRaw("");
    setResponseParsed(null);
    setError("");
  };

  const handleLoadSample = () => {
    applyScenario(sampleScenario);
    setPlannerNotice("Loaded the sample VRP scenario.");
    setStep(2);
  };

  const handleSaveScenario = () => {
    const trimmed = scenarioName.trim();
    if (!trimmed) {
      setPlannerNotice("Enter a scenario name before saving.");
      return;
    }
    const scenario: SavedScenario = {
      id: typeof crypto !== "undefined" && "randomUUID" in crypto
        ? crypto.randomUUID()
        : `scenario_${Date.now()}`,
      name: trimmed,
      savedAt: new Date().toISOString(),
      data: captureScenario(),
    };
    setSavedScenarios((prev) => [
      scenario,
      ...prev.filter((item) => item.name !== trimmed),
    ]);
    setSelectedScenarioId(scenario.id);
    setScenarioName("");
    setPlannerNotice("Scenario saved locally.");
  };

  const handleLoadSaved = () => {
    const scenario = savedScenarios.find((item) => item.id === selectedScenarioId);
    if (!scenario) {
      setPlannerNotice("Select a saved scenario to load.");
      return;
    }
    applyScenario(scenario.data);
    setPlannerNotice(`Loaded "${scenario.name}".`);
    setStep(2);
  };

  const handleDeleteSaved = () => {
    if (!selectedScenarioId) {
      setPlannerNotice("Select a saved scenario to delete.");
      return;
    }
    setSavedScenarios((prev) => prev.filter((item) => item.id !== selectedScenarioId));
    setSelectedScenarioId("");
    setPlannerNotice("Scenario deleted.");
  };

  const updateVehicle = (index: number, field: keyof VehicleForm, value: string) => {
    setVehicles((prev) =>
      prev.map((vehicle, idx) =>
        idx === index ? { ...vehicle, [field]: value } : vehicle
      )
    );
  };

  const updateTask = (index: number, field: keyof TaskForm, value: string) => {
    setTasks((prev) =>
      prev.map((task, idx) => (idx === index ? { ...task, [field]: value } : task))
    );
  };

  const updateDepot = (index: number, field: keyof DepotForm, value: string) => {
    setDepots((prev) =>
      prev.map((depot, idx) => (idx === index ? { ...depot, [field]: value } : depot))
    );
  };

  const addVehicle = () => {
    setVehicles((prev) => [...prev, createVehicle(prev.length + 1)]);
  };

  const removeVehicle = (index: number) => {
    setVehicles((prev) => prev.filter((_, idx) => idx !== index));
  };

  const addTask = () => {
    setTasks((prev) => [...prev, createTask(prev.length + 1)]);
  };

  const removeTask = (index: number) => {
    setTasks((prev) => prev.filter((_, idx) => idx !== index));
  };

  const addDepot = () => {
    setDepots((prev) => [...prev, createDepot(prev.length + 1)]);
  };

  const removeDepot = (index: number) => {
    setDepots((prev) => prev.filter((_, idx) => idx !== index));
  };

  const runOptimization = async () => {
    setIsLoading(true);
    setError("");
    setResponseRaw("");
    setResponseParsed(null);
    try {
      const res = await fetch(`${apiBase}/v1/optimize`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiKey.trim()}`,
        },
        body: JSON.stringify(payload),
      });
      const text = await res.text();
      setResponseRaw(text);
      const parsed = text ? JSON.parse(text) : null;
      setResponseParsed(parsed);
      if (!res.ok) {
        const msg = parsed?.error?.message || "Optimization failed.";
        throw new Error(msg);
      }
    } catch (err: any) {
      setError(err.message || "Optimization failed.");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="portal-page">
      <div className="portal-header">
        <div>
          <h1>Route Planner</h1>
          <p className="portal-subtitle">
            Build an optimization request and run it against the V1 API.
          </p>
        </div>
        <div className="portal-header-actions">
          <button
            className="button secondary"
            onClick={() => setStep((prev) => Math.max(1, prev - 1))}
            disabled={step === 1}
          >
            Back
          </button>
          <button
            className="button primary"
            onClick={() => setStep((prev) => Math.min(3, prev + 1))}
            disabled={step === 3}
          >
            Next
          </button>
        </div>
      </div>

      <div className="planner-stepper">
        <div className={step === 1 ? "active" : ""}>Step 1 - Define</div>
        <div className={step === 2 ? "active" : ""}>Step 2 - Tasks & Vehicles</div>
        <div className={step === 3 ? "active" : ""}>Step 3 - Run</div>
      </div>

      {step === 1 && (
        <>
          <div className="portal-panel planner-panel">
            <h3>Examples & Saved Scenarios</h3>
            <div className="planner-scenario-grid">
              <button className="button secondary" onClick={handleLoadSample}>
                Load Sample VRP
              </button>
              <p className="planner-scenario-note">
                Sample uses Brussels coordinates so the Belgium-only OSRM
                mapping server can compute distances.
              </p>
              <div className="planner-scenario-row">
                <input
                  value={scenarioName}
                  onChange={(event) => setScenarioName(event.target.value)}
                  placeholder="Scenario name"
                />
                <button className="button primary" onClick={handleSaveScenario}>
                  Save Current
                </button>
              </div>
              <div className="planner-scenario-row">
                <select
                  value={selectedScenarioId}
                  onChange={(event) => setSelectedScenarioId(event.target.value)}
                >
                  <option value="">Select saved scenario</option>
                  {savedScenarios.map((scenario) => (
                    <option key={scenario.id} value={scenario.id}>
                      {scenario.name}
                    </option>
                  ))}
                </select>
                <button className="button secondary" onClick={handleLoadSaved}>
                  Load
                </button>
                <button className="button ghost" onClick={handleDeleteSaved}>
                  Delete
                </button>
              </div>
              {plannerNotice && (
                <p className="planner-scenario-note">{plannerNotice}</p>
              )}
            </div>
          </div>

          <div className="portal-panel planner-panel">
            <h3>Define the problem</h3>
            <div className="form-grid">
              <label>Problem Type</label>
              <select
                value={problemType}
                onChange={(event) => setProblemType(event.target.value)}
              >
                <option value="vrptw">VRPTW</option>
                <option value="vrp">VRP</option>
                <option value="tsp">TSP</option>
              </select>

              <label>Primary Objective</label>
              <select
                value={primaryObjective}
                onChange={(event) => setPrimaryObjective(event.target.value)}
              >
                <option value="minimize_total_duration">Minimize Duration</option>
                <option value="minimize_total_distance">Minimize Distance</option>
              </select>

              <label>Secondary Objective</label>
              <select
                value={secondaryObjective}
                onChange={(event) => setSecondaryObjective(event.target.value)}
              >
                <option value="minimize_total_distance">Minimize Distance</option>
                <option value="minimize_total_duration">Minimize Duration</option>
              </select>

              <label>Default Window Start</label>
              <input
                type="datetime-local"
                value={windowStart}
                onChange={(event) => setWindowStart(event.target.value)}
              />

              <label>Default Window End</label>
              <input
                type="datetime-local"
                value={windowEnd}
                onChange={(event) => setWindowEnd(event.target.value)}
              />
            </div>
          </div>
        </>
      )}

      {step === 2 && (
        <div className="planner-grid">
          <section className="portal-panel">
            <div className="planner-header">
              <h3>Depots</h3>
              <button className="button secondary" onClick={addDepot}>
                Add Depot
              </button>
            </div>
            <div className="planner-list">
              {depots.map((depot, index) => (
                <div key={depot.id} className="planner-item">
                  <div className="planner-item-header">
                    <strong>{depot.id}</strong>
                    {depots.length > 1 && (
                      <button
                        className="button ghost"
                        onClick={() => removeDepot(index)}
                      >
                        Remove
                      </button>
                    )}
                  </div>
                  <div className="form-grid">
                    <label>ID</label>
                    <input
                      value={depot.id}
                      onChange={(event) =>
                        updateDepot(index, "id", event.target.value)
                      }
                    />
                    <label>Name</label>
                    <input
                      value={depot.name}
                      onChange={(event) =>
                        updateDepot(index, "name", event.target.value)
                      }
                    />
                    <label>Lat</label>
                    <input
                      value={depot.lat}
                      onChange={(event) =>
                        updateDepot(index, "lat", event.target.value)
                      }
                    />
                    <label>Lng</label>
                    <input
                      value={depot.lng}
                      onChange={(event) =>
                        updateDepot(index, "lng", event.target.value)
                      }
                    />
                    <label>Address</label>
                    <input
                      value={depot.address}
                      onChange={(event) =>
                        updateDepot(index, "address", event.target.value)
                      }
                    />
                    <label>Window Start</label>
                    <input
                      type="datetime-local"
                      value={depot.windowStart}
                      onChange={(event) =>
                        updateDepot(index, "windowStart", event.target.value)
                      }
                    />
                    <label>Window End</label>
                    <input
                      type="datetime-local"
                      value={depot.windowEnd}
                      onChange={(event) =>
                        updateDepot(index, "windowEnd", event.target.value)
                      }
                    />
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="portal-panel">
            <div className="planner-header">
              <h3>Vehicles</h3>
              <button className="button secondary" onClick={addVehicle}>
                Add Vehicle
              </button>
            </div>
            <div className="planner-list">
              {vehicles.map((vehicle, index) => (
                <div key={vehicle.id} className="planner-item">
                  <div className="planner-item-header">
                    <strong>{vehicle.id}</strong>
                    {vehicles.length > 1 && (
                      <button
                        className="button ghost"
                        onClick={() => removeVehicle(index)}
                      >
                        Remove
                      </button>
                    )}
                  </div>
                  <div className="form-grid">
                    <label>ID</label>
                    <input
                      value={vehicle.id}
                      onChange={(event) =>
                        updateVehicle(index, "id", event.target.value)
                      }
                    />
                    <label>Start Lat</label>
                    <input
                      value={vehicle.startLat}
                      onChange={(event) =>
                        updateVehicle(index, "startLat", event.target.value)
                      }
                    />
                    <label>Start Lng</label>
                    <input
                      value={vehicle.startLng}
                      onChange={(event) =>
                        updateVehicle(index, "startLng", event.target.value)
                      }
                    />
                    <label>Window Start</label>
                    <input
                      type="datetime-local"
                      value={vehicle.windowStart}
                      onChange={(event) =>
                        updateVehicle(index, "windowStart", event.target.value)
                      }
                    />
                    <label>Window End</label>
                    <input
                      type="datetime-local"
                      value={vehicle.windowEnd}
                      onChange={(event) =>
                        updateVehicle(index, "windowEnd", event.target.value)
                      }
                    />
                    <label>Break Start</label>
                    <input
                      type="datetime-local"
                      value={vehicle.breakStart}
                      onChange={(event) =>
                        updateVehicle(index, "breakStart", event.target.value)
                      }
                    />
                    <label>Break End</label>
                    <input
                      type="datetime-local"
                      value={vehicle.breakEnd}
                      onChange={(event) =>
                        updateVehicle(index, "breakEnd", event.target.value)
                      }
                    />
                    <label>Break Duration (min)</label>
                    <input
                      value={vehicle.breakDuration}
                      onChange={(event) =>
                        updateVehicle(index, "breakDuration", event.target.value)
                      }
                    />
                    <label>Max Tasks</label>
                    <input
                      value={vehicle.maxTasks}
                      onChange={(event) =>
                        updateVehicle(index, "maxTasks", event.target.value)
                      }
                    />
                    <label>Skills (comma)</label>
                    <input
                      value={vehicle.skills}
                      onChange={(event) =>
                        updateVehicle(index, "skills", event.target.value)
                      }
                      placeholder="delivery, pickup"
                    />
                    <label>Depot ID</label>
                    <input
                      value={vehicle.depotId}
                      onChange={(event) =>
                        updateVehicle(index, "depotId", event.target.value)
                      }
                      placeholder="depot_1"
                    />
                    <label>Team ID</label>
                    <input
                      value={vehicle.teamId}
                      onChange={(event) =>
                        updateVehicle(index, "teamId", event.target.value)
                      }
                      placeholder="team_alpha"
                    />
                  </div>
                </div>
              ))}
            </div>
          </section>

          <section className="portal-panel">
            <div className="planner-header">
              <h3>Tasks</h3>
              <button className="button secondary" onClick={addTask}>
                Add Task
              </button>
            </div>
            <div className="planner-list">
              {tasks.map((task, index) => (
                <div key={task.id} className="planner-item">
                  <div className="planner-item-header">
                    <strong>{task.id}</strong>
                    {tasks.length > 1 && (
                      <button
                        className="button ghost"
                        onClick={() => removeTask(index)}
                      >
                        Remove
                      </button>
                    )}
                  </div>
                  <div className="form-grid">
                    <label>ID</label>
                    <input
                      value={task.id}
                      onChange={(event) =>
                        updateTask(index, "id", event.target.value)
                      }
                    />
                    <label>Type</label>
                    <input
                      value={task.type}
                      onChange={(event) =>
                        updateTask(index, "type", event.target.value)
                      }
                    />
                    <label>Lat</label>
                    <input
                      value={task.lat}
                      onChange={(event) =>
                        updateTask(index, "lat", event.target.value)
                      }
                    />
                    <label>Lng</label>
                    <input
                      value={task.lng}
                      onChange={(event) =>
                        updateTask(index, "lng", event.target.value)
                      }
                    />
                    <label>Service Duration (min)</label>
                    <input
                      value={task.serviceDuration}
                      onChange={(event) =>
                        updateTask(index, "serviceDuration", event.target.value)
                      }
                    />
                    <label>Window Start</label>
                    <input
                      type="datetime-local"
                      value={task.windowStart}
                      onChange={(event) =>
                        updateTask(index, "windowStart", event.target.value)
                      }
                    />
                    <label>Window End</label>
                    <input
                      type="datetime-local"
                      value={task.windowEnd}
                      onChange={(event) =>
                        updateTask(index, "windowEnd", event.target.value)
                      }
                    />
                    <label>Preferred Start</label>
                    <input
                      type="datetime-local"
                      value={task.preferredWindowStart}
                      onChange={(event) =>
                        updateTask(index, "preferredWindowStart", event.target.value)
                      }
                    />
                    <label>Preferred End</label>
                    <input
                      type="datetime-local"
                      value={task.preferredWindowEnd}
                      onChange={(event) =>
                        updateTask(index, "preferredWindowEnd", event.target.value)
                      }
                    />
                    <label>Soft Penalty</label>
                    <input
                      value={task.softPenalty}
                      onChange={(event) =>
                        updateTask(index, "softPenalty", event.target.value)
                      }
                      placeholder="50"
                    />
                    <label>Priority (1-10)</label>
                    <input
                      value={task.priority}
                      onChange={(event) =>
                        updateTask(index, "priority", event.target.value)
                      }
                    />
                    <label>Required Skills (comma)</label>
                    <input
                      value={task.requiredSkills}
                      onChange={(event) =>
                        updateTask(index, "requiredSkills", event.target.value)
                      }
                      placeholder="delivery"
                    />
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      )}

      {step === 3 && (
        <div className="planner-grid">
          <section className="portal-panel">
            <h3>Optimization Settings</h3>
            <div className="form-grid">
              <label>API Base</label>
              <input
                value={apiBase}
                onChange={(event) => setApiBase(event.target.value)}
              />
              <label>API Key (Bearer)</label>
              <input
                value={apiKey}
                onChange={(event) => setApiKey(event.target.value)}
                placeholder="sk-live-..."
              />
              <label>Max Route Duration (min)</label>
              <input
                value={maxRouteDuration}
                onChange={(event) => setMaxRouteDuration(event.target.value)}
              />
              <label>Max Route Distance (km)</label>
              <input
                value={maxRouteDistance}
                onChange={(event) => setMaxRouteDistance(event.target.value)}
              />
              <label>Max Compute (sec)</label>
              <input
                value={maxCompute}
                onChange={(event) => setMaxCompute(event.target.value)}
              />
              <label>Solution Quality</label>
              <select
                value={solutionQuality}
                onChange={(event) => setSolutionQuality(event.target.value)}
              >
                <option value="balanced">Balanced</option>
                <option value="fast">Fast</option>
                <option value="best">Best</option>
              </select>
              <label>Alternative Solutions</label>
              <input
                value={returnAlternatives}
                onChange={(event) => setReturnAlternatives(event.target.value)}
                placeholder="0"
              />
            </div>

            <div className="planner-toggle-row">
              <label>
                <input
                  type="checkbox"
                  checked={balanceRoutes}
                  onChange={(event) => setBalanceRoutes(event.target.checked)}
                />
                Balance routes across vehicles
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={allowOvertime}
                  onChange={(event) => setAllowOvertime(event.target.checked)}
                />
                Allow overtime (adds slack)
              </label>
              <label>
                <input
                  type="checkbox"
                  checked={calculateCarbon}
                  onChange={(event) => setCalculateCarbon(event.target.checked)}
                />
                Calculate carbon footprint
              </label>
            </div>

            <button
              className="button primary"
              onClick={runOptimization}
              disabled={isLoading}
            >
              {isLoading ? "Running..." : "Run Optimization"}
            </button>
            <p className="planner-map-note">
              To show real road paths, set `NEXT_PUBLIC_OSRM_BASE` for the web
              app (example: `http://localhost:5000`).
            </p>
          </section>

          <section className="portal-panel">
            <h3>Route Map</h3>
            <div className="planner-map" ref={mapRef} />
            <p className="planner-map-note">
              Map preview updates after you run the optimization. Before that,
              it shows your current vehicle and task locations.
            </p>
            {responseParsed?.routes?.length ? (
              <div className="planner-map-legend">
                {responseParsed.routes.map((route: any, index: number) => (
                  <div key={route.vehicle_id} className="planner-legend-item">
                    <span
                      className="planner-legend-swatch"
                      style={{
                        background: ROUTE_COLORS[index % ROUTE_COLORS.length],
                      }}
                    />
                    <span>{route.vehicle_id}</span>
                  </div>
                ))}
              </div>
            ) : null}
          </section>

          <section className="portal-panel">
            <h3>Request Preview</h3>
            <pre className="portal-code-block">
              {JSON.stringify(payload, null, 2)}
            </pre>
          </section>
        </div>
      )}

      {error && <div className="error-box">{error}</div>}

      {responseParsed && (
        <div className="portal-panel">
          <h3>Optimization Results</h3>
          <div className="planner-results">
            <div>
              <strong>Status:</strong> {responseParsed.status || "unknown"}
            </div>
            {responseParsed.metrics && (
              <div className="planner-metrics">
                <div>Total Distance: {responseParsed.metrics.total_distance_km} km</div>
                <div>Total Duration: {responseParsed.metrics.total_duration_minutes} min</div>
                <div>Tasks Assigned: {responseParsed.metrics.tasks_assigned}</div>
                <div>Tasks Unassigned: {responseParsed.metrics.tasks_unassigned}</div>
                {responseParsed.metrics.carbon_kg !== undefined && (
                  <div>Estimated CO₂: {responseParsed.metrics.carbon_kg} kg</div>
                )}
              </div>
            )}
            {responseParsed.routes && (
              <div className="planner-routes">
                {responseParsed.routes.map((route: any) => (
                  <div key={route.vehicle_id} className="planner-route">
                    <strong>{route.vehicle_id}</strong>
                    <div>
                      Distance: {route.total_distance_km} km, Duration:{" "}
                      {route.total_duration_minutes} min
                    </div>
                    {osrmRouteMetrics[route.vehicle_id] && (
                      <div className="planner-route-osrm">
                        Road Distance:{" "}
                        {osrmRouteMetrics[route.vehicle_id].distanceKm.toFixed(2)} km, Road
                        Duration:{" "}
                        {osrmRouteMetrics[route.vehicle_id].durationMin.toFixed(1)} min
                      </div>
                    )}
                    <div>Stops: {route.stops?.length || 0}</div>
                  </div>
                ))}
              </div>
            )}
            {responseParsed.unassigned_tasks?.length > 0 && (
              <div className="planner-unassigned">
                <strong>Unassigned Tasks</strong>
                <ul>
                  {responseParsed.unassigned_tasks.map((task: any) => (
                    <li key={task.task_id}>
                      {task.task_id}: {task.reason}
                    </li>
                  ))}
                </ul>
              </div>
            )}
            {responseParsed.alternative_solutions?.length > 0 && (
              <div className="planner-alternatives">
                <strong>Alternative Solutions</strong>
                <div className="planner-alt-list">
                  {responseParsed.alternative_solutions.map(
                    (solution: any, idx: number) => (
                      <div key={idx} className="planner-alt-card">
                        <div>Quality Score: {solution.quality_score}</div>
                        <div>Routes: {solution.routes?.length || 0}</div>
                        {solution.metrics && (
                          <div>
                            Distance: {solution.metrics.total_distance_km} km
                          </div>
                        )}
                      </div>
                    )
                  )}
                </div>
              </div>
            )}
          </div>
          <h4>Raw Response</h4>
          <pre className="portal-code-block">{responseRaw}</pre>
        </div>
      )}
    </div>
  );
}
